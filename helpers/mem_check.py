from memory_profiler import profile

from langchain_ollama import OllamaLLM
@profile
def test_invoke():
    llama_guard_model = OllamaLLM(model="llama-guard3:1b")
    response = llama_guard_model.invoke("here is some text in the input, can you check what is happenig")
    print(response)

if __name__ == "__main__":
    test_invoke()
