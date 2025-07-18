---
config:
  theme: redux
---
flowchart TD
 subgraph s1["Server architecture (frank-brain)"]
        A(["Task to do in text"])
        n2["Orchestrator"]
        n3["What to do?"]
        n4["Browser check"]
        n5["Count calories"]
        n6["Base on knowledge"]
  end
    A --> n2
    n2 --> n3
    n3 --> n4 & n5 & n6
    n3@{ shape: diam}
