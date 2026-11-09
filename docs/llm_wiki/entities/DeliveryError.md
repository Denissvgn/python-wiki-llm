# DeliveryError

**Location:** `integrations/wiki-candidate/delivery/git_transport.py:46`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [git_transport](../modules/git_transport.md)

## Description

Delivery could not be verified; no local success checkpoint is available.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DeliveryError (integrations/wiki-candidate/delivery/git_transport.py)"]
    n1["ValueError"]
    n2["_checkpoint (integrations/wiki-candidate/delivery/git_transport.py)"]
    n3["_fetch (integrations/wiki-candidate/delivery/git_transport.py)"]
    n4["_git (integrations/wiki-candidate/delivery/git_transport.py)"]
    n5["_oid (integrations/wiki-candidate/delivery/git_transport.py)"]
    n6["_publish (integrations/wiki-candidate/delivery/git_transport.py)"]
    n7["_read (integrations/wiki-candidate/delivery/git_transport.py)"]
    n8["_remote (integrations/wiki-candidate/delivery/git_transport.py)"]
    n9["_resolve (integrations/wiki-candidate/delivery/git_transport.py)"]
    n10["_roll (integrations/wiki-candidate/delivery/git_transport.py)"]
    n11["_session (integrations/wiki-candidate/delivery/git_transport.py)"]
    n12["_Session.check_high_water (integrations/wiki-candidate/delivery/git_transport.py)"]
    n13["_Session.readback (integrations/wiki-candidate/delivery/git_transport.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    n13 --> n0
    click n0 "../modules/git_transport.md"
    click n2 "../modules/git_transport.md"
    click n3 "../modules/git_transport.md"
    click n4 "../modules/git_transport.md"
    click n5 "../modules/git_transport.md"
    click n6 "../modules/git_transport.md"
    click n7 "../modules/git_transport.md"
    click n8 "../modules/git_transport.md"
    click n9 "../modules/git_transport.md"
    click n10 "../modules/git_transport.md"
    click n11 "../modules/git_transport.md"
    click n12 "../modules/git_transport.md"
    click n13 "../modules/git_transport.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [git_transport](../modules/git_transport.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_checkpoint` | call | [git_transport](../modules/git_transport.md) | 7 |
| `_fetch` | call | [git_transport](../modules/git_transport.md) | 1 |
| `_git` | call | [git_transport](../modules/git_transport.md) | 3 |
| `_oid` | call | [git_transport](../modules/git_transport.md) | 1 |
| `_publish` | call | [git_transport](../modules/git_transport.md) | 2 |
| `_read` | call | [git_transport](../modules/git_transport.md) | 5 |
| `_remote` | call | [git_transport](../modules/git_transport.md) | 3 |
| `_resolve` | call | [git_transport](../modules/git_transport.md) | 4 |
| `_roll` | call | [git_transport](../modules/git_transport.md) | 6 |
| `_session` | call | [git_transport](../modules/git_transport.md) | 4 |
| `_Session.check_high_water` | call | [git_transport](../modules/git_transport.md) | 2 |
| `_Session.readback` | call | [git_transport](../modules/git_transport.md) | 1 |

> References: showing 12 of 17 logical references; 5 omitted by the 12-row generated summary limit.
