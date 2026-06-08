# Lusotech SQE Automation: Notes on what's potentially missing

**Better SDK and documentation transparency**

- The SDK documentation does not surface available methods clearly enough to build against confidently, adding to a steep learning curve for engineers new to platforms like this.
Discovering what operations are possible on a workflow object required procedures like iterating through nodes and extracting information manually or iterating over dir() and filtering by keyword, essentially reverse engineering the SDK at runtime rather than reading a reference (see figure below). Having methods which allow you to quickly (or in a "prettier" way) discern acceptable data contracts for inputs and outputs in each node would increase efficiency for development.

<img width="564" height="353" alt="Screenshot 2026-06-08 at 12 19 13" src="https://github.com/user-attachments/assets/ff853828-adcf-499d-8aea-741f1ee43af8" />


**Data Holder Nodes**

- A node that holds a value, closer to a variable declaration than a transformation, could make complex workflows significantly more maintainable. One that holds or aliases data and can serve as both an output reference point and an input source downstream. This would allow intermediate values to be named, pinned, and reused across multiple branches without having to re-extract or re-compute them. I had to mock a data holder node with my "Pass through node" I created.

<img width="303" height="136" alt="Screenshot 2026-06-08 at 12 21 59" src="https://github.com/user-attachments/assets/7c93152e-92a8-4c56-99d5-5cc301fcd614" />

**Multiplicity-Aware Nodes**

- Being able to configure nodes to be able to accept one or many inputs of the same type and handle the iteration implicitly, would significantly simplify pipeline design for batched workloads. For example, being able to have multiple files in a file input node and each one processed with outputs collected accordingly. 


**Frontend Stability**

- When configuring nodes on the frontend, scrollable modals occasionally exhibited a jarring snap-back behaviour, scrolling down to reach interactive elements at the bottom would cause the modal to jump back to the top upon clicking, making those options effectively unreachable without repeated attempts. It may be that it is a Safari-specific issue however but thought it was worth mentioning for usability! Refer to the video below:

https://github.com/user-attachments/assets/d7a5b804-ae6e-48a8-92a4-def3ea870235

