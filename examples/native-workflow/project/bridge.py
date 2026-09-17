"""An on-demand host bridge using only the installed public API."""

import json

from llm_wiki_cli import api


class WorkflowBridge:
    def __init__(self, *, sessions=True):
        self.sessions = sessions
        self.session = None
        self.request = None
        self.last = None
        self.unsaved = False

    def start(self, request):
        self.close()
        self.request = json.loads(json.dumps(request))
        self.session = api.open_context_session(src_dir="src", wiki_dir="wiki") if self.sessions else None
        self.unsaved = False

    def event(self, kind, *, unsaved_buffers=False):
        if kind not in {"saved", "branch-changed", "cancelled", "buffers"}:
            raise ValueError("Unsupported host event")
        if type(unsaved_buffers) is not bool:
            raise ValueError("unsaved_buffers must be a boolean")
        if kind == "cancelled":
            self.close()
            return
        self.unsaved = unsaved_buffers
        if self.session is not None:
            self.session.hint(unsaved_buffers=unsaved_buffers)

    def before_decision(self):
        if self.request is None:
            raise ValueError("Start an explicit task first")
        if self.unsaved:
            raise ValueError("Save or defer unsaved buffers")
        if self.session is None:
            context = api.build_task_context(self.request, src_dir="src", wiki_dir="wiki")
        else:
            reply = self.session.read(self.request)
            context = reply.context
        if context is None or not context.ok:
            raise ValueError("Context cannot fit; reduce requirements or revise the host budget")
        api.validate_task_context(context.rendered, self.request)
        self.last = context
        return context  # The host decides whether to include these bytes.

    def handoff(self, explanation):
        if self.last is None or not isinstance(explanation, str) or len(explanation) > 8192:
            raise ValueError("Read context and supply a bounded durable explanation")
        return {"schema_version": "example-workflow-handoff/v1", "request": self.request,
                "context": self.last.rendered, "explanation": explanation}

    def resume(self, handoff):
        if handoff.get("schema_version") != "example-workflow-handoff/v1":
            raise ValueError("Unknown handoff schema")
        self.start(handoff["request"])
        result = api.reconcile_task_context(handoff["context"], handoff["request"], src_dir="src", wiki_dir="wiki")
        self.last = result.pop("context")
        if not self.last.ok:
            raise ValueError("Resumed context cannot fit")
        return result

    def close(self):
        if self.session is not None:
            self.session.close()
        self.session = self.request = self.last = None
