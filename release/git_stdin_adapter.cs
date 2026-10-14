// External Windows Git I/O adapter. Provider/archive/harness bytes stay intact.
using System;
using System.Diagnostics;
using System.Text;

internal static class GitStdinAdapter
{
    private static bool IdentityProbe(string[] a)
    {
        if (a.Length < 4 || a[0] != "-C") return false;
        if (a.Length == 6 && a[2] == "rev-parse" &&
            a[3] == "--absolute-git-dir" && a[4] == "--git-path" && a[5] == "index") return true;
        if (a.Length == 5 && a[2] == "rev-parse" && a[3] == "--verify" && a[4] == "HEAD") return true;
        return a.Length == 5 && a[2] == "symbolic-ref" && a[3] == "-q" && a[4] == "HEAD";
    }

    // Windows CRT argv quoting, including literal quotes and trailing slashes.
    private static string Quote(string value)
    {
        StringBuilder b = new StringBuilder("\"");
        int slashes = 0;
        foreach (char c in value)
        {
            if (c == '\\') { slashes++; continue; }
            if (c == '"') { b.Append('\\', slashes * 2 + 1); b.Append('"'); }
            else { b.Append('\\', slashes); b.Append(c); }
            slashes = 0;
        }
        b.Append('\\', slashes * 2); b.Append('"');
        return b.ToString();
    }

    private static int Main(string[] args)
    {
        string real = Environment.GetEnvironmentVariable("AGENT_WIKI_REAL_GIT");
        if (String.IsNullOrEmpty(real)) { Console.Error.WriteLine("Missing explicit original Git executable"); return 125; }
        StringBuilder command = new StringBuilder();
        foreach (string argument in args) { if (command.Length != 0) command.Append(' '); command.Append(Quote(argument)); }
        bool isolated = IdentityProbe(args);
        ProcessStartInfo info = new ProcessStartInfo(real, command.ToString());
        info.UseShellExecute = false;
        info.RedirectStandardInput = isolated;
        // stdout/stderr and all explicitly owned input commands pass through.
        using (Process child = Process.Start(info))
        {
            if (isolated) child.StandardInput.Close();
            child.WaitForExit();
            return child.ExitCode;
        }
    }
}
