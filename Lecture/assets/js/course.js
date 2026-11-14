/* The course manifest. Adding a lecture = one entry here + one lectures/lecNNN.html file. */
window.COURSE = {
  title: "AI Engineering: Building with LLMs",
  modules: [
    { title: "Module 0: Foundations", lectures: [
      { n: 1, title: "Setup and First Check", minutes: 45 },
      { n: 2, title: "Python Primer for AI Engineers", minutes: 60 },
      { n: 3, title: "HTTP and the Raw API Call", minutes: 45 },
    ]},
    { title: "Module 1: Talking to an LLM", lectures: [
      { n: 4, title: "The SDK and Model Parameters", minutes: 45 },
      { n: 5, title: "Messages and Roles", minutes: 45 },
      { n: 6, title: "Message Content Blocks", minutes: 45 },
      { n: 7, title: "Streaming", minutes: 40 },
      { n: 8, title: "Prompt Engineering Basics", minutes: 60 },
      { n: 9, title: "Response Formatting", minutes: 60 },
      { n: 10, title: "Building a CLI App", minutes: 50 },
      { n: 11, title: "Reliability", minutes: 60 },
    ]},
    { title: "Module 2: LangChain", lectures: [
      { n: 12, title: "LangChain Chat Models", minutes: 40 },
      { n: 13, title: "Prompts and Chains", minutes: 50 },
      { n: 14, title: "Structured Output in LangChain", minutes: 45 },
      { n: 15, title: "Streamlit Chat App", minutes: 60 },
    ]},
    { title: "Module 3: Tool Calling", lectures: [
      { n: 16, title: "Tool Calling by Hand", minutes: 60 },
      { n: 17, title: "Tools in LangChain", minutes: 45 },
      { n: 18, title: "CLI Calling", minutes: 60 },
    ]},
    { title: "Module 4: RAG", lectures: [
      { n: 19, title: "Embeddings and Similarity", minutes: 50 },
      { n: 20, title: "Loading and Chunking", minutes: 50 },
      { n: 21, title: "Vector Store with Chroma", minutes: 45 },
      { n: 22, title: "The RAG Chain", minutes: 60 },
      { n: 23, title: "Better Retrieval", minutes: 75 },
      { n: 24, title: "Evaluating RAG", minutes: 75 },
      { n: 25, title: "Chat With Your Docs", minutes: 75 },
    ]},
    { title: "Module 5: Agents with LangGraph", lectures: [
      { n: 26, title: "LangGraph Basics", minutes: 60 },
      { n: 27, title: "An Agent from Scratch", minutes: 60 },
      { n: 28, title: "Memory and Persistence", minutes: 70 },
      { n: 29, title: "Human in the Loop", minutes: 70 },
      { n: 30, title: "Agentic RAG", minutes: 75 },
      { n: 31, title: "Multi-Agent Systems", minutes: 75 },
    ]},
    { title: "Module 6: MCP", lectures: [
      { n: 32, title: "MCP Concepts and Using a Server", minutes: 60 },
      { n: 33, title: "Build Your Own MCP Server", minutes: 60 },
      { n: 34, title: "Agent with Multiple MCP Servers", minutes: 60 },
    ]},
    { title: "Module 7: Toward Production", lectures: [
      { n: 35, title: "Observability and Cost", minutes: 60 },
      { n: 36, title: "Safety and Guardrails", minutes: 75 },
      { n: 37, title: "Capstone: Nimbus Helpdesk", minutes: 240 },
    ]},
    { title: "Module 8: Beyond the Capstone", lectures: [
      { n: 38, title: "Evaluating Agents", minutes: 60 },
      { n: 39, title: "Conversation Memory Strategies", minutes: 60 },
      { n: 40, title: "Deploying the Capstone", minutes: 90 },
    ]},
  ],
};
