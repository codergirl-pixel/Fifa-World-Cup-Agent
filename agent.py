import os
import json
import time
import wikipediaapi
import requests
from openai import OpenAI
from ddgs import DDGS

client = OpenAI(
    api_key=os.environ["GITHUB_TOKEN"],
    base_url="https://models.inference.ai.azure.com",
)

MEMORY_FILE = "memory.json"

# --- Dashboard stats ---
stats = {
    "conversation_turns": 0,
    "memory_entries": 0,
    "wikipedia_lookups": 0,
    "web_searches": 0,
    "response_times": [],
    "last_tool_used": "None",
    "cache_hits": 0,
    "current_topic": "None",
    "current_player": "None",
}

# --- Simple cache ---
cache = {}

def print_dashboard():
    avg_time = (
        round(sum(stats["response_times"]) / len(stats["response_times"]), 1)
        if stats["response_times"] else 0.0
    )
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 40)
    print("       FIFA World Cup Agent")
    print("=" * 40)
    print(f"  Conversation turns   : {stats['conversation_turns']}")
    print(f"  Memory entries       : {stats['memory_entries']}")
    print(f"  Wikipedia lookups    : {stats['wikipedia_lookups']}")
    print(f"  Web searches         : {stats['web_searches']}")
    print(f"  Avg response time    : {avg_time} s")
    print(f"  Last tool used       : {stats['last_tool_used']}")
    print(f"  Cache hits           : {stats['cache_hits']}")
    print(f"  Current topic        : {stats['current_topic']}")
    print(f"  Current player       : {stats['current_player']}")
    print("=" * 40)
    print()

# --- Load memory from file ---
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            entries = data.get("summary", "").strip().split("\n")
            stats["memory_entries"] = len([e for e in entries if e.strip()])
            return data.get("summary", "")
    return ""

# --- Save memory to file ---
def save_memory(conversation_history):
    print("\n[Saving memory...]")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history + [
                {
                    "role": "user",
                    "content": "Summarize the key facts and topics we discussed in this conversation in bullet points. Be concise."
                }
            ],
            timeout=30,
        )
        summary = response.choices[0].message.content
        with open(MEMORY_FILE, "w") as f:
            json.dump({"summary": summary}, f, indent=2)
        entries = summary.strip().split("\n")
        stats["memory_entries"] = len([e for e in entries if e.strip()])
        print("[Memory saved!]\n")
    except Exception as e:
        print(f"[Could not save memory: {e}]\n")

# --- Update current topic and player from reply ---
def update_context(reply):
    try:
        context_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"From this text, extract:\n1. The main FIFA World Cup tournament being discussed (e.g. '2006 FIFA World Cup') or 'None'\n2. The main player being discussed (e.g. 'Zinedine Zidane') or 'None'\n\nRespond ONLY in this exact JSON format with no extra text:\n{{\"topic\": \"...\", \"player\": \"...\"}}\n\nText: {reply}"
                }
            ],
            timeout=30,
        )
        raw = context_response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        if data.get("topic") and data["topic"] != "None":
            stats["current_topic"] = data["topic"]
        if data.get("player") and data["player"] != "None":
            stats["current_player"] = data["player"]
    except Exception:
        pass  # silently skip if context extraction fails

# --- Tool functions ---
def web_search(query):
    """Search with automatic retry on failure using a simplified query."""
    # First attempt
    try:
        if query in cache:
            stats["cache_hits"] += 1
            return cache[query]
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if results:
            output = ""
            for r in results:
                output += f"Title: {r['title']}\nSummary: {r['body']}\nURL: {r['href']}\n\n"
            cache[query] = output
            return output
    except Exception:
        pass

    # First attempt failed — try a shorter simplified query
    print(f"[Search failed for '{query}' — retrying with simplified query...]")
    try:
        short_query = " ".join(query.split()[:4])  # use first 4 words only
        if short_query in cache:
            stats["cache_hits"] += 1
            return cache[short_query]
        with DDGS() as ddgs:
            results = list(ddgs.text(short_query, max_results=3))
        if results:
            output = ""
            for r in results:
                output += f"Title: {r['title']}\nSummary: {r['body']}\nURL: {r['href']}\n\n"
            cache[short_query] = output
            print(f"[Retry succeeded with '{short_query}']")
            return output
    except Exception:
        pass

    # Both attempts failed
    print("[Both search attempts failed — notifying user]")
    return "SEARCH_FAILED: I was unable to find verified information on this topic after two attempts. Please let the user know you could not verify this fact and suggest they check a reliable source like FIFA.com or Wikipedia directly."
def wikipedia_lookup(topic):
    if topic in cache:
        stats["cache_hits"] += 1
        return cache[topic]
    wiki = wikipediaapi.Wikipedia(
        language="en",
        user_agent="fifa-agent/1.0"
    )
    page = wiki.page(topic)
    if not page.exists():
        return f"No Wikipedia page found for '{topic}'."
    result = f"Title: {page.title}\nSummary: {page.summary[:500]}...\nURL: {page.fullurl}"
    cache[topic] = result
    return result

def live_football_scores():
    api_key = os.environ.get("FOOTBALL_API_KEY", "")
    if not api_key:
        return "Football API key not set."
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": api_key}
    params = {"status": "LIVE,FINISHED", "limit": 5}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return f"Could not fetch scores. Status: {response.status_code}"
        data = response.json()
        matches = data.get("matches", [])
        if not matches:
            return "No recent matches found."
        output = ""
        for match in matches:
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            home_score = match["score"]["fullTime"]["home"]
            away_score = match["score"]["fullTime"]["away"]
            status = match["status"]
            date = match["utcDate"][:10]
            output += f"{date} | {home} {home_score} - {away_score} {away} [{status}]\n"
        return output.strip()
    except Exception as e:
        return f"Error fetching scores: {str(e)}"

# --- Tell the model about the tools ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information about FIFA World Cup news, results, fixtures, and stats.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query to look up."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_lookup",
            "description": "Look up detailed background information on a FIFA World Cup topic such as a player, team, tournament, or stadium on Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic to look up on Wikipedia."}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "live_football_scores",
            "description": "Fetch the latest FIFA World Cup match scores and results.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

# --- Tool dispatcher ---
def run_tool(name, arguments):
    if name == "web_search":
        stats["web_searches"] += 1
        stats["last_tool_used"] = "Web Search"
        return web_search(arguments["query"])
    elif name == "wikipedia_lookup":
        stats["wikipedia_lookups"] += 1
        stats["last_tool_used"] = "Wikipedia"
        return wikipedia_lookup(arguments["topic"])
    elif name == "live_football_scores":
        stats["last_tool_used"] = "Live Scores"
        return live_football_scores()
    return "Tool not found."

# --- Load memory and build system prompt ---
memory = load_memory()
memory_context = f"\n\nHere is a summary of previous conversations with the user:\n{memory}" if memory else ""

conversation_history = [
    {
        "role": "system",
        "content": f"You are a helpful assistant that specializes in the FIFA World Cup. Answer questions about World Cup history, teams, players, tournaments, results, and records. Use the web_search tool for current news and live info. Use the wikipedia_lookup tool for detailed background info on players, teams, and tournaments. If a question is not related to the FIFA World Cup, politely let the user know you can only help with World Cup topics. Before giving your final answer, always explain your reasoning step by step using this format:\n\n🧠 Reasoning: [your thinking here]\n✅ Answer: [your final answer here]\n\nFor specific historical facts such as captains, scorers, dates, and records, always verify using the web_search or wikipedia_lookup tool before answering. Never state specific facts from memory alone. If you are not 100% certain about a specific fact, always say 'Based on my knowledge...' or 'I believe...' before answering and suggest the user verify it. If a tool returns a message starting with 'SEARCH_FAILED:', inform the user clearly that you could not verify the information and suggest they check FIFA.com or Wikipedia directly for accurate details.{memory_context}"
    }
]

# --- Main loop ---
print_dashboard()

while True:
    user_input = input("Prompt: ")
    if user_input.lower() == "quit":
        save_memory(conversation_history)
        break

    conversation_history.append({
        "role": "user",
        "content": f"{user_input}\n\n[Important: If this question involves a specific historical fact, name, date, record, or statistic, you MUST verify it using web_search or wikipedia_lookup before answering. Do not rely on memory alone.]"
    })

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            tools=tools,
            tool_choice="auto",
            timeout=30,
        )
    except Exception as e:
        print(f"Connection error: {e}\nPlease try again.\n")
        conversation_history.pop()
        continue

    message = response.choices[0].message

    if message.tool_calls:
        conversation_history.append(message)

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"[Using tool: {name} → {list(arguments.values())[0] if arguments else ''}]")
            result = run_tool(name, arguments)
            conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        try:
            followup = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation_history,
                timeout=30,
            )
            agent_reply = followup.choices[0].message.content
        except Exception as e:
            print(f"Connection error: {e}\nPlease try again.\n")
            continue
    else:
        agent_reply = message.content

    # --- Update stats ---
    elapsed = round(time.time() - start_time, 1)
    stats["response_times"].append(elapsed)
    stats["conversation_turns"] += 1

    conversation_history.append({"role": "assistant", "content": agent_reply})

    # Update topic and player in background
    update_context(agent_reply)

    # Refresh dashboard then print reply
    print_dashboard()
    print(f"Agent: {agent_reply}\n")