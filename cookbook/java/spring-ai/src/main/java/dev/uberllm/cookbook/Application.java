package dev.uberllm.cookbook;

import java.util.List;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

/**
 * Spring AI ChatClient on UberLLM: a call, a stream, a tool call and a typed
 * entity. The base URL and key are in application.properties.
 *
 * <pre>
 * export UBERLLM_API_KEY=ull_...
 * mvn spring-boot:run
 * </pre>
 */
@SpringBootApplication
public class Application {

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    /** A tool the model can call. Replace the body with a real weather API. */
    static class WeatherTools {
        @Tool(description = "Get the current weather for a city")
        String getWeather(@ToolParam(description = "City name") String city) {
            return "{\"city\":\"" + city + "\",\"celsius\":21,\"sky\":\"clear\"}";
        }
    }

    record Movie(String title, int year, List<String> directors) {}

    @Bean
    CommandLineRunner run(ChatClient.Builder builder) {
        return args -> {
            ChatClient chat = builder.build();

            // 1. One reply
            System.out.println(chat.prompt("What is a context window? One sentence.").call().content());

            // 2. Streaming
            chat.prompt("Count from 1 to 5, separated by commas.")
                .stream()
                .content()
                .doOnNext(System.out::print)
                .blockLast();
            System.out.println();

            // 3. Tool calling: Spring AI runs the tool and sends the result back
            System.out.println(chat.prompt("What's the weather in Paris?")
                .tools(new WeatherTools())
                .call()
                .content());

            // 4. Typed output
            Movie movie = chat.prompt("The 1999 film where Neo takes the red pill.")
                .call()
                .entity(Movie.class);
            System.out.println(movie);
        };
    }
}
