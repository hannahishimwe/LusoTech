# Lusotech SQE Automation: Notes on what's potentially missing

**Better SDK and documentation transparency**

- The SDK documentation does not surface available methods clearly enough to build against confidently, adding to a steep learning curve for engineers new to platforms like this.
Discovering what operations are possible on a workflow object required iterating over dir() and filtering by keyword, essentially reverse engineering the SDK at runtime rather than reading a reference. 

**Data Holder Nodes**

- A node that holds a value, closer to a variable declaration than a transformation, could make complex workflows significantly more maintainable. One that holds or aliases data and can serve as both an output reference point and an input source downstream. This would allow intermediate values to be named, pinned, and reused across multiple branches without having to re-extract or re-compute them. 

**Multiplicity-Aware Nodes**

- Being able to configure nodes to be able to accept one or many inputs of the same type and handle the iteration implicitly, would significantly simplify pipeline design for batched workloads. For example, being able to have multiple files in a file input node and each one processed with outputs collected accordingly. 

**Frontend Stability**

- When configuring nodes on the frontend, scrollable modals occasionally exhibited a jarring snap-back behaviour, scrolling down to reach interactive elements at the bottom would cause the modal to jump back to the top upon clicking, making those options effectively unreachable without repeated attempts. This may be a Safari-specific issue however but thought it was worth mentioning!

