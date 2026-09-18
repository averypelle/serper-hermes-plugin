# serper-hermes-plugin

A [Hermes Agent](https://hermes-agent.nousresearch.com/) web-search backend plugin
for [Serper](https://serper.dev/) — Google Search results via a simple JSON API.

Serper is **search-only**; pair it with Firecrawl / Tavily / Exa / Parallel for
`web_extract`.

## Install

Drop the plugin into your user plugin directory:

```bash
git clone https://github.com/averypelle/serper-hermes-plugin.git \
  ~/.hermes/plugins/serper
```

Add your API key to `~/.hermes/.env` (get one at <https://serper.dev/api-key> —
Serper gives 2,500 free queries on signup):

```
SERPER_API_KEY=your_key_here
```

Then either run `hermes tools` and pick **Serper (Google Search)** under
*Web Search & Extract*, or edit `~/.hermes/config.yaml` directly:

```yaml
web:
  search_backend: "serper"
  extract_backend: "firecrawl"   # any extract-capable provider
```

Verify:

```bash
hermes plugins list          # should show "web-serper" enabled
hermes setup                 # should report "✅ Web Search & Extract (serper)"
```

## Optional configuration

Extra knobs, all via environment variables (no config schema needed):

| Env var          | Purpose                                    | Example |
| ---------------- | ------------------------------------------ | ------- |
| `SERPER_API_KEY` | **Required.** Your Serper API key.         | `sk-…`  |
| `SERPER_GL`      | Country code for geo-localized results.    | `us`    |
| `SERPER_HL`      | UI/results language.                       | `en`    |

## What you get

Each `web_search` call POSTs to `https://google.serper.dev/search` and maps
Serper's `organic` results into Hermes' standard envelope:

```jsonc
{
  "success": true,
  "data": {
    "web": [
      { "title": "...", "url": "...", "description": "...", "position": 1 },
      // ...
    ]
  }
}
```

When Serper returns an `answerBox` with a link, it's folded in as the top result.

## Files

```
serper-hermes-plugin/
├── __init__.py     # register(ctx) entry point
├── provider.py     # SerperWebSearchProvider
├── plugin.yaml     # manifest (kind: backend, provides_web_providers: [serper])
├── LICENSE
└── README.md
```

## Development

Validate the plugin loads cleanly:

```bash
hermes plugins doctor ~/.hermes/plugins/serper --ci
```

## License

MIT © Avery Pelle. See [LICENSE](LICENSE).

Not affiliated with Nous Research or Serper.
