<p align="center">
<img src="https://i.imgur.com/exiipaG.png" width="1000px" />
<br>
<a href="https://discord.gg/pqEHdWDf8z"><img src="https://i.imgur.com/VMdA0q7.png" height="60px"/> </a>
<a href="https://www.nexusmods.com/skyrimspecialedition/mods/111491"><img src="https://i.imgur.com/STsBXT6.png" height="60px"/> </a>
<a href="https://docs.moddingforge.com/sse-at"><img src="https://i.imgur.com/NFNG8Tb.png" height="60px"/> </a>
<a href="https://ko-fi.com/cutleast"><img src="https://i.imgur.com/KcPrhK5.png" height="60px"/> </a>
<br>
</p>

## Description

SSE Auto Translator is a standalone Windows app that allows you to translate entire mod lists with a high degree of automation. Its main features include an automatic mod list scan that identifies the mods that need translation. SSE-AT is then able to automatically search [Nexus Mods](https://www.nexusmods.com/) (and [La Confrérie des Traducteurs](https://www.confrerie-des-traducteurs.fr/) for French translations) for available translations, download them, and convert them to DSD format. The downloaded translations are then combined into a new mod (the so-called Output Mod) and installed at the end of your mod list. In addition, SSE Auto Translator offers an integrated editor that can be used to edit downloaded translations and create new ones.

## Usage

See [Documentation > Quick Start & Basic Usage](https://docs.moddingforge.com/sse-at/quick_start.html).

## Features

See [Documentation > Introduction](https://docs.moddingforge.com/sse-at/index.html#_features) for a full list of features.

## Limitations

See [Documentation > Introduction](https://docs.moddingforge.com/sse-at/index.html#_limitations) for a full list of limitations.

## FAQ

See [Documentation > FAQs](https://docs.moddingforge.com/sse-at/faqs.html) for a full list of frequently asked questions.

## Contributing

### 1. Feedback (Suggestions/Issues)

If you encountered an issue/error or you have a suggestion, create an issue under the "Issues" tab above.

### 2. Code contributions

#### 1. Install requirements

1. Install [Python 3.14](https://www.python.org/downloads/) (Make sure that you add it to PATH!)
2. Install [uv](https://github.com/astral-sh/uv#installation)
3. Clone repository and all submodules with `git clone https://github.com/Cutleast/SSE-Auto-Translator --recurse-submodules`
4. Open terminal in repository folder
5. Run the following command to init your local environment and to install all dependencies: `uv sync`
6. Run the following command to build SSE-AT and compile the required resource file: `build.bat`

#### 2. Execute from source

1. Open terminal in repository folder
2. Execute main file with uv: `uv run src\main.py`

#### 3. Compile and build executable

1. Run `build.bat` from the root folder of this repo.
2. The executable and all dependencies are built in the `dist/SSE-AT`-Folder and gets packed in a `dist/SSE-AT v[version].zip`.

### 3. Beta-Testing

If you are interested in testing pre-release versions of SSE-AT, join our Discord server above.

### 4. Maintaining a Masterlist

If you're interested in maintaining a masterlist for your language, contact us (@cutleast or @whusten) on our Discord server linked above!

## Credits

- Qt by [The Qt Company Ltd](https://qt.io)
- [lingua-py](https://github.com/pemistahl/lingua-py) by [Peter M. Stahl](https://github.com/pemistahl)
- [Nuitka](https://github.com/Nuitka/Nuitka)
- [DynamicStringDistributor](https://github.com/SkyHorizon3/SSE-Dynamic-String-Distributor) by [SkyHorizon](https://github.com/SkyHorizon3)
- Icon by [Wuerfelhusten](https://nexusmods.com/users/122160268)
- Editor QoL Improvements by [FuchieSteph](https://github.com/FuchieSteph)
- Other used software and libraries:
  - Open SSE-AT > Help > About > Used Software
  - Alternatively: [licenses.py](./src/core/utilities/licenses.py)
- Test data used (only distributed with the source code and used for automated tests in [tests](./tests/)):
  - [Obsidian Weathers and Seasons](https://www.nexusmods.com/skyrimspecialedition/mods/12125) by [DrJacopo](https://next.nexusmods.com/profile/DrJacopo)
  - [Obsidian Weathers and Seasons - German](https://www.nexusmods.com/skyrimspecialedition/mods/16286) by [Hilli1](https://next.nexusmods.com/profile/Hilli1)
  - [Ordinator - Perks of Skyrim](https://www.nexusmods.com/skyrimspecialedition/mods/1137) by [Enai Siaion](https://next.nexusmods.com/profile/EnaiSiaion)
  - [RS Children Overhaul](https://www.nexusmods.com/skyrimspecialedition/mods/2650) by [isophe](https://next.nexusmods.com/profile/isophe)
  - [Wet and Cold SE](https://www.nexusmods.com/skyrimspecialedition/mods/644) by [StepModifications](https://next.nexusmods.com/profile/StepModifications)
  - [Wet and Cold SE - German](https://www.nexusmods.com/skyrimspecialedition/mods/89391) by [kroenel](https://next.nexusmods.com/profile/kroenel)
  - `_ResourcePack.esl & _ResourcePack.bsa` by Bethesda from the Vanilla base game, stripped down to the bare minimum

## OpenAI-Compatible LLM Translation

SSE-AT provides one generic `LLM` translator integration for OpenAI-compatible
chat-completions APIs. It can be used with local or hosted servers without
provider-specific translator implementations. This includes Unsloth, Ollama,
LM Studio, Gemini through its OpenAI-compatible endpoint, and other servers
that implement `GET /models` and `POST /chat/completions`.

### Settings

Select `LLM` as the translator API in Settings and configure the following
fields:

- **LLM API URL**: The OpenAI-compatible base URL, including its version path.
  Examples: `http://127.0.0.1:8888/v1` for Unsloth,
  `http://127.0.0.1:11434/v1` for Ollama,
  `http://127.0.0.1:1234/v1` for LM Studio, and
  `https://generativelanguage.googleapis.com/v1beta/openai` for Gemini.
- **Translator API key**: Sent as a Bearer token. It is required by the
  application; local servers that do not validate authentication can use a
  non-secret placeholder value.
- **LLM model**: Use **Refresh models** to request the server's `/models`
  endpoint, then choose one of the returned model IDs.
- **System prompt**: One shared, editable instruction for LLM translation. The
  default prompt preserves Skyrim terminology, formatting, placeholders,
  markup, control sequences, and the selected Russian addressing style.
- **Reasoning**: `Off` is the default and sends `reasoning_effort: "none"`.
  `Auto` omits the field; Minimal, Low, Medium, and High send the corresponding
  value for servers that support it.

The integration sends non-streaming requests to `/chat/completions` with a low
temperature. It returns only the translated text and reports invalid URLs,
missing credentials/model/prompt, network errors, and API error messages in
the application UI. Translation-cache keys include the URL, model, prompt,
reasoning setting, input text, target language, and glossary version, so a
change to output-affecting settings does not reuse an incompatible cached
translation.

### Official Vanilla Glossary

When `LLM` is used, SSE-AT lazily builds an in-memory glossary from the bundled
vanilla translation database for the selected target language. It includes
named plugin fields (`* FULL`) such as NPCs, locations, quests, items,
factions, books, spells, shouts, perks, races, and equipment, plus quest
objectives (`QUST NNAM`). No separate glossary file is created.

Before a request, SSE-AT finds exact English terms in the text being translated
and appends up to 20 relevant pairs to the system prompt. For example:

```text
- Windhelm -> Виндхельм
- Ulfric Stormcloak -> Ульфрик Буревестник
- Stones of Barenziah -> Камень Барензии
```

The LLM is instructed to treat these values as authoritative Skyrim
terminology while adapting grammatical case and singular/plural number to the
target sentence. Regular English plural variants for names in the form
`<word> of <name>` are generated automatically, allowing `Stones of Barenziah`
to be matched from the vanilla `Stone of Barenziah` entry. The glossary is
built only once per application session when LLM translation is first used;
matching is local and adds no network or GPU workload.
