//! Chat, streaming and a tool-calling loop on UberLLM with the async-openai crate.
//!
//!     export UBERLLM_API_KEY=ull_...
//!     cargo run
//!
//! Any OpenAI-compatible client works with UberLLM: point the base URL at
//! https://api.uberllm.dev/v1 and use your ull_ key.
use std::{env, error::Error, io::Write};

use async_openai::{
    config::OpenAIConfig,
    types::chat::{
        ChatCompletionMessageToolCalls, ChatCompletionRequestAssistantMessageArgs,
        ChatCompletionRequestMessage, ChatCompletionRequestToolMessageArgs,
        ChatCompletionRequestUserMessageArgs, ChatCompletionTool, ChatCompletionTools,
        CreateChatCompletionRequestArgs, FunctionObjectArgs,
    },
    Client,
};
use futures::StreamExt;
use serde_json::{json, Value};

fn get_weather(city: &str) -> Value {
    json!({ "city": city, "celsius": 21, "sky": "clear" }) // replace with a real weather API
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let config = OpenAIConfig::new()
        .with_api_base("https://api.uberllm.dev/v1")
        .with_api_key(env::var("UBERLLM_API_KEY")?);
    let client = Client::with_config(config);
    let model = env::var("UBERLLM_MODEL").unwrap_or_else(|_| "deepseek/deepseek-v4-flash".into());

    // 1. One reply
    let request = CreateChatCompletionRequestArgs::default()
        .model(&model)
        .messages([ChatCompletionRequestUserMessageArgs::default()
            .content("What is a context window? One sentence.")
            .build()?
            .into()])
        .build()?;
    let response = client.chat().create(request).await?;
    println!("{}", response.choices[0].message.content.as_deref().unwrap_or(""));
    if let Some(usage) = &response.usage {
        println!("tokens in/out: {}/{}", usage.prompt_tokens, usage.completion_tokens);
    }

    // 2. Streaming
    let request = CreateChatCompletionRequestArgs::default()
        .model(&model)
        .messages([ChatCompletionRequestUserMessageArgs::default()
            .content("Count from 1 to 5, separated by commas.")
            .build()?
            .into()])
        .build()?;
    let mut stream = client.chat().create_stream(request).await?;
    while let Some(chunk) = stream.next().await {
        for choice in chunk?.choices {
            if let Some(text) = choice.delta.content {
                print!("{text}");
            }
        }
        std::io::stdout().flush()?;
    }
    println!();

    // 3. Tool calling, full loop
    let tools = vec![ChatCompletionTools::Function(ChatCompletionTool {
        function: FunctionObjectArgs::default()
            .name("get_weather")
            .description("Get the current weather for a city.")
            .parameters(json!({
                "type": "object",
                "properties": { "city": { "type": "string" } },
                "required": ["city"]
            }))
            .build()?,
    })];
    let mut messages: Vec<ChatCompletionRequestMessage> = vec![ChatCompletionRequestUserMessageArgs::default()
        .content("What's the weather in Paris?")
        .build()?
        .into()];

    for _round in 0..5 {
        let request = CreateChatCompletionRequestArgs::default()
            .model(&model)
            .messages(messages.clone())
            .tools(tools.clone())
            .build()?;
        let message = client.chat().create(request).await?.choices.remove(0).message;
        let calls = message.tool_calls.unwrap_or_default();
        if calls.is_empty() {
            println!("{}", message.content.unwrap_or_default());
            break;
        }
        messages.push(
            ChatCompletionRequestAssistantMessageArgs::default()
                .tool_calls(calls.clone())
                .build()?
                .into(),
        );
        for call in calls {
            if let ChatCompletionMessageToolCalls::Function(call) = call {
                let args: Value = serde_json::from_str(&call.function.arguments)?;
                let result = get_weather(args["city"].as_str().unwrap_or_default());
                println!("-> {}({}) = {}", call.function.name, args, result);
                messages.push(
                    ChatCompletionRequestToolMessageArgs::default()
                        .tool_call_id(call.id)
                        .content(result.to_string())
                        .build()?
                        .into(),
                );
            }
        }
    }
    Ok(())
}
