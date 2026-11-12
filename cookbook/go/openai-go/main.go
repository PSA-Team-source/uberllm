// Chat, streaming and tool calling with the official OpenAI Go SDK
// (github.com/openai/openai-go/v3) on UberLLM.
//
//	export UBERLLM_API_KEY=ull_...
//	go run .
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/option"
)

func main() {
	client := openai.NewClient(
		option.WithBaseURL("https://api.uberllm.dev/v1"),
		option.WithAPIKey(os.Getenv("UBERLLM_API_KEY")),
	)
	model := os.Getenv("UBERLLM_MODEL")
	if model == "" {
		model = "deepseek/deepseek-v4-flash"
	}
	ctx := context.Background()

	// 1. One reply
	resp, err := client.Chat.Completions.New(ctx, openai.ChatCompletionNewParams{
		Model: model,
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.UserMessage("What is a context window? One sentence."),
		},
	})
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(resp.Choices[0].Message.Content)
	// UberLLM adds usage.cost_usd (US dollars); read it from the raw JSON.
	fmt.Println("cost:", resp.Usage.JSON.ExtraFields["cost_usd"].Raw())

	// 2. Streaming
	stream := client.Chat.Completions.NewStreaming(ctx, openai.ChatCompletionNewParams{
		Model:    model,
		Messages: []openai.ChatCompletionMessageParamUnion{openai.UserMessage("Count from 1 to 5, separated by commas.")},
	})
	for stream.Next() {
		if c := stream.Current(); len(c.Choices) > 0 {
			fmt.Print(c.Choices[0].Delta.Content)
		}
	}
	if err := stream.Err(); err != nil {
		log.Fatal(err)
	}
	fmt.Println()

	// 3. Tool calling, full loop
	params := openai.ChatCompletionNewParams{
		Model: model,
		Messages: []openai.ChatCompletionMessageParamUnion{
			openai.UserMessage("What's the weather in Paris?"),
		},
		Tools: []openai.ChatCompletionToolUnionParam{
			openai.ChatCompletionFunctionTool(openai.FunctionDefinitionParam{
				Name:        "get_weather",
				Description: openai.String("Get the current weather for a city."),
				Parameters: openai.FunctionParameters{
					"type":       "object",
					"properties": map[string]any{"city": map[string]string{"type": "string"}},
					"required":   []string{"city"},
				},
			}),
		},
	}
	for round := 0; round < 5; round++ {
		r, err := client.Chat.Completions.New(ctx, params)
		if err != nil {
			log.Fatal(err)
		}
		msg := r.Choices[0].Message
		if len(msg.ToolCalls) == 0 {
			fmt.Println(msg.Content)
			break
		}
		params.Messages = append(params.Messages, msg.ToParam())
		for _, call := range msg.ToolCalls {
			var args struct{ City string }
			if err := json.Unmarshal([]byte(call.Function.Arguments), &args); err != nil {
				log.Fatal(err)
			}
			result := fmt.Sprintf(`{"city":%q,"celsius":21,"sky":"clear"}`, args.City) // replace with a real API
			fmt.Println("->", call.Function.Name, args.City)
			params.Messages = append(params.Messages, openai.ToolMessage(result, call.ID))
		}
	}
}
