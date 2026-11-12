// Chat, streaming and a tool-calling loop on UberLLM with the official
// OpenAI .NET SDK (NuGet: OpenAI).
//
//   export UBERLLM_API_KEY=ull_...
//   dotnet run
using System.ClientModel;
using System.Text.Json;
using OpenAI;
using OpenAI.Chat;

var apiKey = Environment.GetEnvironmentVariable("UBERLLM_API_KEY")
    ?? throw new InvalidOperationException("Set UBERLLM_API_KEY");
var model = Environment.GetEnvironmentVariable("UBERLLM_MODEL") ?? "deepseek/deepseek-v4-flash";

ChatClient client = new(
    model,
    new ApiKeyCredential(apiKey),
    new OpenAIClientOptions { Endpoint = new Uri("https://api.uberllm.dev/v1") });

// 1. One reply
ChatCompletion reply = client.CompleteChat("What is a context window? One sentence.");
Console.WriteLine(reply.Content[0].Text);
Console.WriteLine($"tokens in/out: {reply.Usage.InputTokenCount}/{reply.Usage.OutputTokenCount}");

// 2. Streaming
foreach (StreamingChatCompletionUpdate update in client.CompleteChatStreaming("Count from 1 to 5, separated by commas."))
{
    foreach (ChatMessageContentPart part in update.ContentUpdate)
    {
        Console.Write(part.Text);
    }
}
Console.WriteLine();

// 3. Tool calling, full loop
ChatTool getWeather = ChatTool.CreateFunctionTool(
    functionName: "get_weather",
    functionDescription: "Get the current weather for a city.",
    functionParameters: BinaryData.FromString("""
        { "type": "object", "properties": { "city": { "type": "string" } }, "required": ["city"] }
        """));

List<ChatMessage> messages = [new UserChatMessage("What's the weather in Paris?")];
ChatCompletionOptions options = new() { Tools = { getWeather } };

for (var round = 0; round < 5; round++)
{
    ChatCompletion completion = client.CompleteChat(messages, options);
    if (completion.FinishReason != ChatFinishReason.ToolCalls)
    {
        Console.WriteLine(completion.Content[0].Text);
        break;
    }
    messages.Add(new AssistantChatMessage(completion));
    foreach (ChatToolCall call in completion.ToolCalls)
    {
        using JsonDocument input = JsonDocument.Parse(call.FunctionArguments);
        var city = input.RootElement.GetProperty("city").GetString();
        // Replace with a real weather API.
        var result = JsonSerializer.Serialize(new { city, celsius = 21, sky = "clear" });
        Console.WriteLine($"-> {call.FunctionName}({city}) = {result}");
        messages.Add(new ToolChatMessage(call.Id, result));
    }
}
