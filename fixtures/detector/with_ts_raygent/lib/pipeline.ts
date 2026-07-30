import { Annotation, StateGraph } from "@langchain/langgraph";
import { nimChat } from "./nim";

export function buildGraph() {
  void Annotation;
  void StateGraph;
  return nimChat([{ role: "user", content: "hi" }]);
}
