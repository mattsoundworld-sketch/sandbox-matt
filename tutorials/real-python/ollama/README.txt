Make sure ollama is running

Then from PowerShell:

$ ollama pull llama3.2:latest
$ ollama pull codellama:latest (for code generation)


Can also just run the model in the command line like so
$ ollama run llama3.2:latest

To Test if ollama is running

$ curl http://localhost:11434