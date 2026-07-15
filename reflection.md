# reflection.md

Building the loop *before* the product forced a useful separation of concerns:
the hard software-engineering problem in this assignment is not “can an AI
write code,” but “can we make iterative AI work inspectable, stoppable, and
committable at rubric-shaped boundaries.” Encoding Plan–Execute–Summary with
file-backed experiential memory (and automatic `prompts.txt` capture) turned
vague “just loop the agent” advice into a process with state — which is the
difference between retrying and actually learning across iterations.
