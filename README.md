# Claude Code Python

涓€涓潰鍚戜唬鐮佸伐浣滅殑 AI CLI / REPL / MCP 椤圭洰锛屾彁渚?Claude Code 椋庢牸鐨勪氦浜掋€佸伐鍏疯皟鐢ㄣ€佷换鍔¤繍琛屾椂銆丄gent銆佸 Provider 鎺ュ叆锛屼互鍙婁竴濂楁寔缁紨杩涗腑鐨勫伐绋嬪寲鍩虹璁炬柦銆?

鏈?README 鏄綋鍓嶄粨搴撶殑缁熶竴鍏ュ彛銆傚ぇ浣撻噺涓撻鏂囨。缁х画淇濈暀鍦?`docs/`锛岃繖閲屽彧淇濈暀蹇呰鎽樿銆佹槑纭鑸拰鍚庣画缁存姢绾﹀畾锛岄伩鍏嶆枃妗ｅ啀娆″け鎺с€?

## 椤圭洰瀹氫綅

- 璇█涓庤繍琛屾椂锛歅ython 3.10+銆乣asyncio`
- 涓诲叆鍙ｏ細`python -m claude_code.main` 鎴?`python run.py`
- 浜や簰妯″紡锛氫氦浜掑紡 REPL銆佸崟娆?query銆佺閬撴ā寮忋€丮CP 鏈嶅姟鍣ㄦā寮?
- 妯″瀷鎺ュ叆锛歚anthropic`銆乣openai`銆乣ollama`銆乣vllm`銆乣deepseek`銆乣bedrock`銆乣vertex`
- 鍏抽敭瀛愮郴缁燂細`QueryEngine`銆乣ToolRegistry`銆佹潈闄愮郴缁熴€佷换鍔¤繍琛屾椂銆丄gent銆丮CP銆佹妧鑳界郴缁熴€佹湇鍔″眰

褰撳墠浠ｇ爜涓?`azure` 璺緞鏈夋樉寮?fail-fast 鎻愮ず锛屽洜姝よ繖閲屼笉鎶婂畠浣滀负褰撳墠鎺ㄨ崘杩愯璺緞銆?

## 褰撳墠鏁寸悊缁撹

鎴嚦 `2026-04-17`锛屾湰浠撳簱鐨?Markdown 鏂囨。鍙互鏀舵暃涓轰互涓嬬粨鏋勶細

1. `README.md` 鍙礋璐ｇ粺涓€鍏ュ彛锛屼笉鍐嶅爢鐮岃秴闀挎暀绋嬪拰瀹炵幇鏋氫妇銆?
2. 鈥滃綋鍓嶇姸鎬佲€濅紭鍏堢湅甯︽棩鏈熺殑璇勪及/鎵ц鏂囨。锛岃€屼笉鏄洿鏃╃殑璇勫鑽夌銆?
3. `docs/current/reference/AGENT.MD` 涓?`docs/current/reference/MCP.md` 浣撻噺杈冨ぇ锛屼繚鐣欑嫭绔嬫枃妗ｏ紝涓嶅啀閲嶅鎼繘 README銆?
4. 鏋舵瀯銆佹€ц兘銆佷腑闂翠欢涓夋潯绾垮垎鍒繚鐣欌€滃綋鍓嶇粨璁衡€濅笌鈥滃巻鍙茬粏鑺傗€濅袱灞傦紝涓嶅啀骞跺垪鍫嗗彔澶氫釜鍚岀骇鍏ュ彛銆?

鏈棰濆鏍稿缁撴灉锛?

- 娴嬭瘯澶嶆牳锛歚pytest -q -c pytest.ini` 閫氳繃锛岀粨鏋滀负 `90 passed`
- 鏋舵瀯鏈€鏂板揩鐓э細`2026-04-16` 鐨勮瘎娴嬬粨璁轰负鈥滃伐绋嬪彲鐢ㄥ熀绾垮彲鎺ㄨ繘鈥濓紝璇勫垎 `8.4 / 10`
- 涓棿浠舵紨杩涘揩鐓э細`Phase 0` 宸插畬鎴愶紝`Phase 1` 鎸佺画鎺ㄨ繘
- 鎬ц兘蹇収锛歚Baseline V1` 璁板綍鍚姩鑰楁椂绾?`1109.38 ms`

## 蹇€熷紑濮?

### 1. 瀹夎渚濊禆

```bash
python -m pip install -r requirements.txt
```

濡傛灉浣犲彧鏄粠婧愮爜杩愯锛屾湰浠撳簱褰撳墠寤鸿浠?`requirements.txt` 鍜?`pytest.ini` 涓哄噯銆?

### 2. 閫夋嫨 Provider

#### Anthropic

```bash
export CLAUDE_API_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your-key
export CLAUDE_MODEL=claude-sonnet-4-20250514
```

#### Ollama / 鏈湴 OpenAI 鍏煎妯″瀷

```bash
export CLAUDE_API_PROVIDER=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
export CLAUDE_MODEL=qwen2.5:14b
```

璇存槑锛?

- `openai` / `deepseek` 闇€瑕?`OPENAI_API_KEY`
- `ollama` / `vllm` 鍏佽鏈湴妯″瀷璺緞锛屼笉寮哄埗鐪熷疄 API Key
- PowerShell 璇峰皢 `export` 鏀逛负 `$env:鍙橀噺鍚?"鍊?`

### Windows 鎺ㄨ崘鍚姩锛堥伩鍏?WindowsApps stub锛?

Windows 涓婁笉瑕佷緷璧?`C:\Users\<you>\AppData\Local\Microsoft\WindowsApps\python.exe` 杩欑被 Store alias stub銆?

寤鸿浼樺厛浣跨敤锛?

```powershell
py -3 -m claude_code.main --doctor
py -3 -m claude_code.main
```

鎴栨樉寮忎娇鐢ㄨ櫄鎷熺幆澧冭В閲婂櫒锛?

```powershell
.\.venv\Scripts\python.exe -m claude_code.main --doctor
.\.venv\Scripts\python.exe -m claude_code.main
```

`--doctor` 浼氳緭鍑鸿В閲婂櫒鏉ユ簮涓庨闄╂彁绀猴紱鑻ュ懡涓?WindowsApps stub锛屼細缁欏嚭鏄庣‘璀﹀憡涓庢浛浠ｅ惎鍔ㄥ懡浠ゃ€?

### 3. 甯哥敤鍚姩鏂瑰紡

```bash
# 鏌ョ湅甯姪
python -m claude_code.main --help

# 鐗堟湰
python -m claude_code.main --version

# 鍋ュ悍妫€鏌?
python -m claude_code.main --doctor

# 浜や簰寮?REPL
python -m claude_code.main

# 鍗曟鎻愰棶
python -m claude_code.main "瑙ｉ噴褰撳墠鐩綍涓嬬殑椤圭洰缁撴瀯"

# 绠￠亾妯″紡
echo "甯垜鎬荤粨杩欐浠ｇ爜" | python -m claude_code.main --pipe

# 浣滀负 MCP 鏈嶅姟鍣ㄥ惎鍔?
python -m claude_code.main --mcp-serve

# 鍚姩鏈湴 daemon / API 鎺у埗闈紙P1-01锛?
python -m claude_code.main --daemon-serve --daemon-host 127.0.0.1 --daemon-port 8787

# CLI 浠?thin-client 璧?daemon锛圥1-06锛?
python -m claude_code.main --daemon-client "explain current repo status"
echo "summarize changed files" | python -m claude_code.main --pipe --daemon-client
```

## 鏍稿績鑳藉姏姒傝

- 浜や簰灞傦細REPL銆佸崟杞?query銆佺閬撴ā寮忋€佸懡浠ょ郴缁?
- 宸ュ叿灞傦細鏂囦欢璇诲啓銆佹悳绱€丼hell/PowerShell銆佸伐浣滄祦銆佷换鍔℃帶鍒躲€佹妧鑳姐€佹祻瑙堝櫒銆丩SP銆丮CP銆乄orktree銆丆ron銆乀eam
- 杩愯鏃讹細`QueryEngine` 缂栨帓妯″瀷瀵硅瘽銆佸伐鍏疯皟鐢ㄣ€佹潈闄愬垽瀹氬拰涓婁笅鏂囨瀯寤?
- 浠诲姟浣撶郴锛歚TaskManager`銆乣TaskRepository`銆乣TaskQueue` 鏀拺鍚庡彴浠诲姟鍜屼换鍔″瓨鍌ㄦ紨杩?
- 鏈嶅姟灞傦細缂撳瓨銆侀€熺巼闄愬埗銆侀仴娴嬨€佸巻鍙茬鐞嗐€佽蹇嗐€佸姞瀵嗐€乭ooks銆乻hutdown銆乼oken estimation
- 鎵╁睍鑳藉姏锛歁CP server/client銆丄gent銆佹妧鑳界洰褰曘€侀」鐩骇 `.claude/` 杩愯鏁版嵁

濡傛灉浣犺鐪嬪畬鏁村伐鍏锋竻鍗曪紝涓嶅啀浠?README 鏌ユ壘锛岀洿鎺ョ湅 `docs/current/reference/MCP.md`銆?

## 浠撳簱缁撴瀯

```text
claude-code-python/
鈹溾攢鈹€ claude_code/          # 涓讳唬鐮?
鈹?  鈹溾攢鈹€ main.py           # CLI 鍏ュ彛
鈹?  鈹溾攢鈹€ engine/           # QueryEngine / context / session / permissions
鈹?  鈹溾攢鈹€ tools/            # 宸ュ叿绯荤粺
鈹?  鈹溾攢鈹€ commands/         # 鍛戒护绯荤粺
鈹?  鈹溾攢鈹€ tasks/            # 浠诲姟杩愯鏃躲€佷粨鍌ㄣ€侀槦鍒?
鈹?  鈹溾攢鈹€ services/         # 缂撳瓨銆侀仴娴嬨€佸巻鍙层€乭ooks銆乻hutdown 绛?
鈹?  鈹溾攢鈹€ mcp/              # MCP 鏈嶅姟绔疄鐜?
鈹?  鈹溾攢鈹€ agents/           # 鍐呯疆 Agent 瀹氫箟
鈹?  鈹溾攢鈹€ skills/           # 鎶€鑳界郴缁?
鈹?  鈹斺攢鈹€ state/            # 鐘舵€佹ā鍨?
鈹溾攢鈹€ docs/                 # 涓撻鏂囨。
鈹溾攢鈹€ examples/             # 绀轰緥鑴氭湰
鈹溾攢鈹€ scripts/              # 杈呭姪鑴氭湰涓庢€ц兘鑴氭湰
鈹溾攢鈹€ tests/                # 娴嬭瘯
鈹溾攢鈹€ run.py                # 婧愮爜杩愯鍏ュ彛
鈹溾攢鈹€ requirements.txt      # 渚濊禆娓呭崟
鈹斺攢鈹€ pytest.ini            # pytest 閰嶇疆
```

## 鏂囨。鍦板浘

涓嬮潰鏄暣鐞嗗悗鐨勬帹鑽愰槄璇婚『搴忋€?

| 鏂囨。 | 瑙掕壊 | 浠€涔堟椂鍊欑湅 | 褰撳墠瀹氫綅 |
|---|---|---|---|
| `README.md` | 鎬诲叆鍙?| 绗竴娆¤繘鍏ヤ粨搴?| 鍞竴瀵艰埅鍏ュ彛 |
| `docs/current/architecture/ARCHITECTURE_EVALUATION_2026-04-16.md` | 鏋舵瀯鐜扮姸蹇収 | 鎯崇煡閬撻」鐩幇鍦ㄦ暣浣撶姸鎬?| 鏋舵瀯涓诲叆鍙?|
| `docs/current/architecture/CLAUDE_CODE_SUPERSEDE_STRATEGY_2026-04-29.md` | 浜у搧鎴樼暐涓庤秴杞﹁矾绾垮浘 | 鎯崇煡閬撻」鐩浣曚粠鈥滃彲鐢ㄥ簳鐩樷€濊蛋鍒扳€滆秴瓒?Claude Code鈥?| 鎴樼暐涓诲叆鍙?|
| `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` | 鎵ц璁″垝涓庝换鍔″崱鍗?| 鎯崇洿鎺ュ紑宸ュ苟鏄庣‘姣忓紶鍗＄殑鐮斿彂鑼冨洿銆佸畬鎴愭爣鍑嗐€佹祴璇曟繁搴?| 鎵ц涓诲叆鍙?|
| `docs/current/middleware/MIDDLEWARE_EVOLUTION_EXECUTION_2026-04-16.md` | 浠诲姟/涓棿浠惰惤鍦拌褰?| 鎯崇煡閬撲换鍔＄郴缁熷凡鏀瑰埌鍝竴姝?| 涓棿浠剁幇鐘朵富鍏ュ彛 |
| `docs/current/performance/PERFORMANCE_ONE_PAGER.md` | 鎬ц兘涓€椤电焊 | 鎯冲揩閫熺湅鎬ц兘鐘舵€?| 鎬ц兘涓诲叆鍙?|
| `docs/current/reference/MCP.md` | MCP 浣跨敤鎵嬪唽 | 鎯虫妸浠撳簱浣滀负 MCP server 鎺ュ叆 | MCP 涓诲叆鍙?|
| `docs/current/reference/AGENT.MD` | Agent 鍏ㄩ噺鎵嬪唽 | 鎯崇悊瑙?Agent銆佸紓姝ュ瓙浠诲姟銆佸鏅鸿兘浣?| Agent 涓诲叆鍙?|
| `docs/history/architecture/ARCHITECTURE_REVIEW.md` | 棣栬疆闂鐩樼偣 | 鎯宠拷婧渶鍒濆彂鐜颁簡鍝簺闂 | 鏋舵瀯鍘嗗彶鏂囨。 |
| `docs/history/architecture/FIX_PROPOSALS.md` | 淇鏂规搴?| 鎯崇湅鍘嗗彶淇璁捐涓庡閫夋柟妗?| 鏋舵瀯鍘嗗彶鏂囨。 |
| `docs/current/middleware/MIDDLEWARE_EVOLUTION_ASSESSMENT_2026-04-16.md` | 涓棿浠舵紨杩涜瘎浼?| 鎯宠瘎浼?Redis/MySQL/骞冲彴鍖栨槸鍚︽湁蹇呰 | 涓棿浠跺喅绛栨枃妗?|
| `docs/history/performance/PERFORMANCE_TOP_TIER_EVALUATION_PLAN.md` | 鎬ц兘璺嚎鍥?| 鎯崇湅闃舵鐩爣鍜屾墽琛岃鍒?| 鎬ц兘璺嚎鍥?|
| `docs/history/performance/PERFORMANCE_OPTIMIZATION_REPORT.md` | 鎬ц兘浼樺寲鏄庣粏 | 鎯宠拷韪叿浣撴敼浜嗗摢浜涚儹璺緞 | 鎬ц兘缁嗚妭鏂囨。 |
| `docs/history/performance/OPTIMIZATION_PROGRESS.md` | 鎬ц兘杩涘害璁板綍 | 鎯崇湅闃舵鎬ц繘灞?| 鎬ц兘鍘嗗彶鏂囨。 |
| `docs/current/performance/BASELINE_V1.md` | 鎬ц兘鍩虹嚎鎽樿 | 鎯崇湅鍩虹嚎缁撹 | 鎬ц兘鏁版嵁鎽樿 |
| `docs/current/performance/baseline_v1.json` | 鍘熷鍩虹嚎鏁版嵁 | 鎯冲仛瀵规瘮鎴栬嚜鍔ㄥ寲澶勭悊 | 鎬ц兘鍘熷鏁版嵁 |

## 鍚勪富棰樼殑鏉冨▉鍏ュ彛

涓洪伩鍏嶁€滃悓涓€涓婚澶氫釜鍏ュ彛鍚屾椂鏈夋晥鈥濓紝鍚庣画缁熶竴鎸変笅闈㈢殑涓诲叆鍙ｇ悊瑙ｏ細

- 鏋舵瀯鐜扮姸锛歚docs/current/architecture/ARCHITECTURE_EVALUATION_2026-04-16.md`
- 浜у搧鎴樼暐 / 瓒呰秺 Claude Code 璺嚎鍥撅細`docs/current/architecture/CLAUDE_CODE_SUPERSEDE_STRATEGY_2026-04-29.md`
- 鎵ц璁″垝 / 浠诲姟鍗″崟锛歚docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 鏋舵瀯鍘嗗彶闂涓庝慨澶嶅閫夛細`docs/history/architecture/ARCHITECTURE_REVIEW.md` + `docs/history/architecture/FIX_PROPOSALS.md`
- 浠诲姟/涓棿浠跺綋鍓嶈惤鍦扮姸鎬侊細`docs/current/middleware/MIDDLEWARE_EVOLUTION_EXECUTION_2026-04-16.md`
- 浠诲姟/涓棿浠舵紨杩涘喅绛栦緷鎹細`docs/current/middleware/MIDDLEWARE_EVOLUTION_ASSESSMENT_2026-04-16.md`
- 鎬ц兘褰撳墠鐘舵€侊細`docs/current/performance/PERFORMANCE_ONE_PAGER.md`
- 鎬ц兘鍩虹嚎鏁版嵁锛歚docs/current/performance/BASELINE_V1.md` + `docs/current/performance/baseline_v1.json`
- MCP 浣跨敤锛歚docs/current/reference/MCP.md`
- Agent 浣跨敤锛歚docs/current/reference/AGENT.MD`

## 鏋舵瀯銆佹€ц兘銆佷腑闂翠欢鐨勬憳瑕?

### 鏋舵瀯

缁煎悎 `docs/current/architecture/ARCHITECTURE_EVALUATION_2026-04-16.md` 涓庡巻鍙茶瘎瀹℃枃妗ｏ紝鐩墠鍙互灏嗘灦鏋勭粨璁烘敹鏁涗负锛?

- 鏂瑰悜涓婃槸鍚堢悊鐨勬ā鍧楀寲鍗曚綋
- 鍏抽敭涓婚摼璺浘鍑虹幇杩囧伐鍏锋毚闇层€佹潈闄愮‖闂搞€丄gent 寮傛銆丳rovider 閫傞厤绛夋柇鐐?
- 鎴嚦 `2026-04-16` 鐨勮瘎娴嬫枃妗ｏ紝杩欎簺鍏抽敭鏂偣宸插畬鎴愪竴杞棴鐜慨澶嶏紝娴嬭瘯璁板綍涓?`68 passed`
- 鏇存棭鐨?`docs/history/architecture/ARCHITECTURE_REVIEW.md` 鍜?`docs/history/architecture/FIX_PROPOSALS.md` 涓昏鐢ㄤ簬杩芥函鈥滀负浠€涔堜細杩欎箞鏀光€濓紝涓嶅啀浠ｈ〃鏈€鏂扮姸鎬?

### 涓棿浠?/ 浠诲姟绯荤粺

缁煎悎涓や唤涓棿浠舵枃妗ｏ紝褰撳墠缁撹鏄細

- 浠撳簱鍘熷妯″瀷鏄€滆繘绋嬪唴闃熷垪 + 鏂囦欢鎸佷箙鍖栤€濓紝涓嶆槸鏁版嵁搴撻槦鍒楁灦鏋?
- 瀵瑰崟鏈?CLI 鍚堢悊锛屼絾瀵瑰钩鍙板寲銆佸瀹炰緥銆佸彲鎭㈠鍦烘櫙椋庨櫓杈冮珮
- 褰撳墠钀藉湴閲嶇偣宸蹭粠鈥滄槸鍚︾珛鍒讳笂 Redis/MySQL鈥濊浆涓衡€滃厛鎶婁换鍔℃ā鍨嬨€佷粨鍌ㄣ€侀槦鍒楁娊璞℃敹鏁涒€?
- 宸插畬鎴愮殑宸ヤ綔鍖呮嫭锛歚tasks.json` schema 缁熶竴銆佹枃浠堕攣銆佸畨鍏ㄥ啓鍏ャ€乨urable 璇箟淇銆乣TaskRepository` / `TaskQueue` 鎶借薄鎺ュ叆

### 鎬ц兘

缁煎悎鎬ц兘鏂囨。锛屽綋鍓嶇粨璁烘槸锛?

- 宸插缓绔嬭娉曢棬绂併€佹€ц兘 smoke銆佸熀绾胯剼鏈笁浠跺熀纭€璁炬柦
- 褰撳墠鍩虹嚎涓绘暟鎹 `docs/current/performance/baseline_v1.json`
- 鍗曢〉鎽樿浼樺厛鐪?`docs/current/performance/PERFORMANCE_ONE_PAGER.md`
- 璇︾粏浼樺寲椤逛紭鍏堢湅 `docs/history/performance/PERFORMANCE_OPTIMIZATION_REPORT.md`

## 寮€鍙戜笌楠岃瘉

```bash
# 杩愯娴嬭瘯
python -m pytest -q -c pytest.ini

# 杩愯 Phase 0 涓婚摼鍥炲綊闂ㄧ锛堟彁浜ゅ墠/鍚堝苟鍓嶏級
python scripts/run_phase0_gate.py

# 杩愯 Phase 1 鎺у埗闈㈠洖褰掗棬绂侊紙P1-01锛?
python scripts/run_p1_control_plane_gate.py

# 杩愯 Phase 1 浜嬩欢鏃ュ織鍥炲綊闂ㄧ锛圥1-02锛?
python scripts/run_p1_event_journal_gate.py

# 杩愯 Phase 1 SQLite 鐘舵€佸悗绔洖褰掗棬绂侊紙P1-03锛?
python scripts/run_p1_sqlite_state_backend_gate.py

# 杩愯 Phase 1 Active Memory 鍥炲綊闂ㄧ锛圥1-04锛?
python scripts/run_p1_active_memory_gate.py

# 杩愯 Phase 1 Hook/Permission/Audit 鏀舵暃闂ㄧ锛圥1-05锛?
python scripts/run_p1_hook_permission_audit_gate.py

# 杩愯 Phase 1 CLI thin-client 杩佺Щ闂ㄧ锛圥1-06锛?
python scripts/run_p1_cli_thin_client_gate.py

# 杩愯 Phase 2 澶?Agent Supervisor 闂ㄧ锛圥2-01锛?
python scripts/run_p2_multi_agent_supervisor_gate.py

# 杩愯 Phase 2 Artifact Bus 闂ㄧ锛圥2-02锛?
python scripts/run_p2_artifact_bus_gate.py

# 杩愯 Phase 2 IDE 闆嗘垚闂ㄧ锛圥2-03锛?
python scripts/run_p2_ide_integration_gate.py

# 杩愯 Phase 2 GitHub/CI workflow 闂ㄧ锛圥2-04锛?
python scripts/run_p2_github_ci_workflow_gate.py

# 杩愯 Phase 2 缁勭粐绛栫暐涓庡璁￠棬绂侊紙P2-05锛?
python scripts/run_p2_org_policy_audit_gate.py

# 杩愯 Phase 2 Agent 杩愯鏃朵竴鑷存€ч棬绂侊紙P2-07锛?
python scripts/run_p2_agent_runtime_parity_gate.py

# 杩愯 Phase 2 鑷畾涔?Agent 鐩綍鍔犺浇闂ㄧ锛圥2-08锛?
python scripts/run_p2_custom_agents_loader_gate.py

# 杩愯 Phase 2 JetBrains IDE 闆嗘垚闂ㄧ锛圥2-10锛?
python scripts/run_p2_jetbrains_ide_integration_gate.py

# 杩愯 Phase 0-2 Linux 缁熶竴楠屽案闂ㄧ锛圥2-06锛?
python scripts/run_linux_unified_gate.py

# 杩愯 Phase 2 Linux 缁熶竴楠屽案鎵ц闂ㄧ锛圥2-09锛孡inux 鎵ц锛?
python scripts/run_p2_linux_unified_execution_gate.py --dry-run
python scripts/run_p2_linux_unified_execution_gate.py --continue-on-failure
# 鍒嗙墖骞惰绀轰緥锛? 涓?job 涓殑绗?2 鐗囷級
python scripts/run_p2_linux_unified_execution_gate.py --shard-total 3 --shard-index 2 --continue-on-failure

# 鑱氬悎澶氬垎鐗?summary 骞剁粰鍑哄叏灞€閫氳繃/澶辫触鍒ゅ畾锛圥2-12锛孡inux 鍥炴敹闃舵鎵ц锛?
python scripts/run_p2_linux_shard_aggregation_gate.py --artifacts-dir .claude/reports
python scripts/run_p2_linux_shard_aggregation_gate.py --summary-glob ".claude/reports/**/summary.json"

# 浠?merged summary 鍙戝竷鏈€缁堟姤鍛婏紙P2-13锛孡inux 鍥炴敹闃舵鎵ц锛?
python scripts/run_p2_linux_report_publish_gate.py --merged-summary .claude/reports/linux_unified_gate/merged_summary.json
python scripts/run_p2_linux_report_publish_gate.py --merged-summary .claude/reports/linux_unified_gate/merged_summary.json --output-json .claude/reports/linux_unified_gate/final_report.json --output-markdown .claude/reports/linux_unified_gate/final_report.md

# 涓€閿覆鑱旀墽琛?>姹囨€?>鍙戝竷鍏ㄩ摼闂ㄧ锛圥2-14锛孡inux 缂栨帓鍏ュ彛锛?
python scripts/run_p2_linux_unified_pipeline_gate.py --dry-run
python scripts/run_p2_linux_unified_pipeline_gate.py --continue-on-failure --fail-fast
# 浠呭仛姹囨€?鍙戝竷锛堣烦杩囨墽琛岄樁娈碉級
python scripts/run_p2_linux_unified_pipeline_gate.py --skip-execution --summary-glob ".claude/reports/**/summary.json"

# 鐢熸垚 Linux 鍒嗙墖鎵ц璁″垝锛圥2-15锛屼緵 CI fan-out job 鐩存帴娑堣垂锛?
python scripts/run_p2_linux_shard_plan_gate.py --shard-total 4 --dry-run --print-commands
python scripts/run_p2_linux_shard_plan_gate.py --shard-total 4 --output .claude/reports/linux_unified_gate/shard_plan.json --continue-on-failure -- -k runtime

# 鐢熸垚 Linux CI matrix 浜х墿锛圥2-16锛屼緵 CI matrix 鐩存帴娑堣垂锛?
python scripts/run_p2_linux_ci_matrix_gate.py --shard-plan .claude/reports/linux_unified_gate/shard_plan.json --dry-run --print-matrix
python scripts/run_p2_linux_ci_matrix_gate.py --shard-plan .claude/reports/linux_unified_gate/shard_plan.json --output .claude/reports/linux_unified_gate/ci_matrix.json --skip-empty-shards

# 鐢熸垚 Linux CI workflow 璁″垝浜х墿锛圥2-17锛屼緵 fan-out/fan-in job 鐩存帴娑堣垂锛?
python scripts/run_p2_linux_ci_workflow_plan_gate.py --ci-matrix .claude/reports/linux_unified_gate/ci_matrix.json --dry-run --print-plan
python scripts/run_p2_linux_ci_workflow_plan_gate.py --ci-matrix .claude/reports/linux_unified_gate/ci_matrix.json --output .claude/reports/linux_unified_gate/ci_workflow_plan.json

# 灏?workflow 璁″垝娓叉煋涓?GitHub Actions YAML锛圥2-18锛屼緵 CI 鐩存帴鎵ц锛?
python scripts/run_p2_linux_ci_workflow_yaml_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --dry-run --print-yaml
python scripts/run_p2_linux_ci_workflow_yaml_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --output-workflow .github/workflows/linux_unified_gate.yml --output-metadata .claude/reports/linux_unified_gate/ci_workflow_render.json

# 鏍￠獙/鍚屾 workflow 娓叉煋浜х墿婕傜Щ锛圥2-19锛岄槻姝?plan->yaml 婕傜Щ锛?
python scripts/run_p2_linux_ci_workflow_sync_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --metadata-path .claude/reports/linux_unified_gate/ci_workflow_render.json --print-diff
python scripts/run_p2_linux_ci_workflow_sync_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --metadata-path .claude/reports/linux_unified_gate/ci_workflow_render.json --write

# 鏍￠獙/瑙勮寖鍖?workflow 璁″垝涓殑鍛戒护濂戠害锛圥2-20锛岄槻姝?command/parts/璺緞 婕傜Щ锛?
python scripts/run_p2_linux_ci_workflow_command_guard_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_command_guard_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --write --output .claude/reports/linux_unified_gate/ci_workflow_command_guard.json

# 姹囨€?workflow 婕傜Щ + 鍛戒护 + 鍏冩暟鎹缂樻不鐞嗭紙P2-21锛岀敓鎴愬崟涓€娌荤悊缁撹锛?
python scripts/run_p2_linux_ci_workflow_governance_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --metadata-path .claude/reports/linux_unified_gate/ci_workflow_render.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_governance_gate.py --ci-workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --metadata-path .claude/reports/linux_unified_gate/ci_workflow_render.json --output .claude/reports/linux_unified_gate/ci_workflow_governance.json

# 鍙戝竷娌荤悊缁撹涓?CI 鍙秷璐瑰喅绛栵紙P2-22锛岀敓鎴?should_execute_workflow 涓庡彂甯冩姤鍛婏級
python scripts/run_p2_linux_ci_workflow_governance_publish_gate.py --governance-report .claude/reports/linux_unified_gate/ci_workflow_governance.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_governance_publish_gate.py --governance-report .claude/reports/linux_unified_gate/ci_workflow_governance.json --output-json .claude/reports/linux_unified_gate/ci_workflow_governance_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_governance_publish.md

# 灏嗘不鐞嗗彂甯冪粨鏋滄敹鏁涗负鎵ц鍐崇瓥闂搁棬锛圥2-23锛岀粺涓€ execute/blocked 鍒ゅ畾涓庨€€鍑虹瓥鐣ワ級
python scripts/run_p2_linux_ci_workflow_decision_gate.py --governance-publish .claude/reports/linux_unified_gate/ci_workflow_governance_publish.json --workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_decision_gate.py --governance-publish .claude/reports/linux_unified_gate/ci_workflow_governance_publish.json --workflow-plan .claude/reports/linux_unified_gate/ci_workflow_plan.json --workflow-path .github/workflows/linux_unified_gate.yml --on-block skip --output-json .claude/reports/linux_unified_gate/ci_workflow_execution_decision.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_execution_decision.md

# 灏嗘墽琛屽喅绛栨敹鏁涗负鍙皟搴﹀懡浠ゅ绾︼紙P2-24锛岀粺涓€ dispatch-ready/blocked 涓?gh workflow run 鍛戒护锛?
python scripts/run_p2_linux_ci_workflow_dispatch_gate.py --execution-decision .claude/reports/linux_unified_gate/ci_workflow_execution_decision.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_dispatch_gate.py --execution-decision .claude/reports/linux_unified_gate/ci_workflow_execution_decision.json --workflow-ref main --output-json .claude/reports/linux_unified_gate/ci_workflow_dispatch.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_dispatch.md

# 鎵ц璋冨害濂戠害骞惰緭鍑烘渶缁堟墽琛屽洖鎵э紙P2-25锛岀粺涓€ dispatched/blocked/fail 鐨勬墽琛岀粨鏋滐級
python scripts/run_p2_linux_ci_workflow_dispatch_execution_gate.py --dispatch-report .claude/reports/linux_unified_gate/ci_workflow_dispatch.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_dispatch_execution_gate.py --dispatch-report .claude/reports/linux_unified_gate/ci_workflow_dispatch.json --project-root . --output-json .claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.md

# 灏?dispatch 鎵ц缁撴灉鏀舵暃涓?run trace 濂戠害锛圥2-27锛岀粺涓€ run_id/url/poll 鍛戒护涓庣姸鎬侊級
python scripts/run_p2_linux_ci_workflow_dispatch_trace_gate.py --dispatch-execution-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_dispatch_trace_gate.py --dispatch-execution-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_execution.json --poll-now --project-root . --output-json .claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.md

# 绛夊緟 dispatch run 鏀舵暃涓烘渶缁堝畬鎴愬垽瀹氾紙P2-28锛岀粺涓€ completed/in_progress/timeout/failure 璇箟锛?
python scripts/run_p2_linux_ci_workflow_dispatch_completion_gate.py --dispatch-trace-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_dispatch_completion_gate.py --dispatch-trace-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_trace.json --project-root . --poll-interval-seconds 20 --max-polls 15 --output-json .claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.md

# 鍙戝竷 dispatch completion 鐨勭粓灞€缁撹锛圥2-29锛岀粺涓€ promote/hold 鍙戝竷璇箟锛?
python scripts/run_p2_linux_ci_workflow_terminal_publish_gate.py --dispatch-completion-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_terminal_publish_gate.py --dispatch-completion-report .claude/reports/linux_unified_gate/ci_workflow_dispatch_completion.json --output-json .claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_terminal_publish.md

# 灏?terminal publish 鏀舵暃涓?release handoff 濂戠害锛圥2-30锛岀粺涓€ release job 瑙﹀彂璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_handoff_gate.py --terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_handoff_gate.py --terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_terminal_publish.json --target-environment production --release-channel stable --output-json .claude/reports/linux_unified_gate/ci_workflow_release_handoff.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_handoff.md

# 鎵ц release 鏈€缁堣Е鍙戦棬绂侊紙P2-31锛岀粺涓€ release dispatch 鎵ц璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_trigger_gate.py --release-handoff-report .claude/reports/linux_unified_gate/ci_workflow_release_handoff.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_trigger_gate.py --release-handoff-report .claude/reports/linux_unified_gate/ci_workflow_release_handoff.json --release-workflow-path .github/workflows/release.yml --release-workflow-ref main --output-json .claude/reports/linux_unified_gate/ci_workflow_release_trigger.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_trigger.md

# 杩借釜 release trigger 鎵ц鍚庣殑 run 璇箟锛圥2-32锛岀粺涓€ release run trace/poll 鐘舵€侊級
python scripts/run_p2_linux_ci_workflow_release_trace_gate.py --release-trigger-report .claude/reports/linux_unified_gate/ci_workflow_release_trigger.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_trace_gate.py --release-trigger-report .claude/reports/linux_unified_gate/ci_workflow_release_trigger.json --poll-now --project-root . --output-json .claude/reports/linux_unified_gate/ci_workflow_release_trace.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_trace.md

# 绛夊緟 release run 鏀舵暃涓烘渶缁堝畬鎴愬垽瀹氾紙P2-33锛岀粺涓€ release 瀹屾垚鎬佽涔夛級
python scripts/run_p2_linux_ci_workflow_release_completion_gate.py --release-trace-report .claude/reports/linux_unified_gate/ci_workflow_release_trace.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_completion_gate.py --release-trace-report .claude/reports/linux_unified_gate/ci_workflow_release_trace.json --project-root . --poll-interval-seconds 20 --max-polls 15 --output-json .claude/reports/linux_unified_gate/ci_workflow_release_completion.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_completion.md

# 鍙戝竷 release completion 鐨勭粓灞€缁撹锛圥2-34锛岀粺涓€ release finalize/hold 璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_terminal_publish_gate.py --release-completion-report .claude/reports/linux_unified_gate/ci_workflow_release_completion.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_terminal_publish_gate.py --release-completion-report .claude/reports/linux_unified_gate/ci_workflow_release_completion.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.md

# 灏?release terminal publish 鏀舵暃涓烘渶缁?finalization 鍐崇瓥锛圥2-35锛岀粺涓€ finalize/hold/abort 璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_finalization_gate.py --release-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_finalization_gate.py --release-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_terminal_publish.json --on-hold pass --output-json .claude/reports/linux_unified_gate/ci_workflow_release_finalization.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_finalization.md

# 灏?release finalization 鏀舵暃涓烘渶缁?closure 鍙戝竷濂戠害锛圥2-36锛岀粺涓€ close/notify/rollback 璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_closure_gate.py --release-finalization-report .claude/reports/linux_unified_gate/ci_workflow_release_finalization.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_closure_gate.py --release-finalization-report .claude/reports/linux_unified_gate/ci_workflow_release_finalization.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_closure.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_closure.md

# 灏?release closure 鏀舵暃涓烘渶缁堣瘉鎹綊妗ｅ绾︼紙P2-37锛岀粺涓€ archive/publish/block 璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_archive_gate.py --release-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_closure.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_archive_gate.py --release-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_closure.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_archive.md

# 灏?release archive 鏀舵暃涓烘渶缁堝彂甯冨垽璇嶅绾︼紙P2-38锛岀粺涓€ ship/hold/block 璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_verdict_gate.py --release-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_archive.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_verdict_gate.py --release-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_archive.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_verdict.md

# 灏?release verdict 鏀舵暃涓?incident dispatch 鎵ц濂戠害锛圥2-39锛岀粺涓€鍛婅瑙﹀彂璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_incident_gate.py --release-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_incident_gate.py --release-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_verdict.json --incident-repo acme/demo --incident-label release-incident --output-json .claude/reports/linux_unified_gate/ci_workflow_release_incident.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_incident.md

# 灏?release incident 鏀舵暃涓虹粓灞€ terminal verdict 濂戠害锛圥2-40锛岀粺涓€ ship/hold/escalate/block 璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py --release-incident-report .claude/reports/linux_unified_gate/ci_workflow_release_incident.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py --release-incident-report .claude/reports/linux_unified_gate/ci_workflow_release_incident.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.md

# 灏?release terminal verdict 鏀舵暃涓烘渶缁?delivery 濂戠害锛圥2-41锛岀粺涓€ deliver/hold/escalate/block 璇箟锛?
python scripts/run_p2_linux_ci_workflow_release_delivery_gate.py --release-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_delivery_gate.py --release-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_terminal_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_delivery.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_delivery.md

# P2-42: converge release delivery to terminal publish contract (announce_release/announce_hold/announce_blocker/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py --release-delivery-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py --release-delivery-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.md

# P2-43: converge release delivery terminal publish to final verdict contract (close_release/open_follow_up/escalate_blocker/abort_close).
python scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py --release-delivery-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py --release-delivery-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_terminal_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.md


# P2-44: converge release delivery final verdict to follow-up dispatch contract (no_action/dispatch_follow_up/dispatch_escalation/abort_dispatch).
python scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py --release-delivery-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py --release-delivery-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.md

# P2-45: converge release follow-up dispatch to follow-up closure contract (no_action/queue_follow_up/queue_escalation/abort_queue).
python scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py --release-follow-up-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py --release-follow-up-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_dispatch.json --follow-up-repo acme/demo --follow-up-label release-follow-up --output-json .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.md

# P2-46: converge release follow-up closure to terminal publish contract (announce_closed/announce_queued/announce_pending_queue/announce_queue_failure/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py --release-follow-up-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py --release-follow-up-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_closure.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.md

# P2-47: converge release follow-up terminal publish to final verdict contract (close_follow_up/keep_follow_up_open/escalate_queue_failure/abort_close).
python scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py --release-follow-up-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py --release-follow-up-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_terminal_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.md

# P2-48: converge delivery/follow-up final verdicts to one release final outcome contract (ship_and_close/ship_with_follow_up_open/escalate_blocker/abort_outcome).
python scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py --release-delivery-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --release-follow-up-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py --release-delivery-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_delivery_final_verdict.json --release-follow-up-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_follow_up_final_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.md

# P2-49: converge release final outcome to terminal publish contract (announce_release_closure/announce_release_with_follow_up/announce_blocker/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py --release-final-outcome-report .claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py --release-final-outcome-report .claude/reports/linux_unified_gate/ci_workflow_release_final_outcome.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.md

# P2-50: converge release final terminal publish to final handoff contract (handoff_release_closure/handoff_release_with_follow_up/handoff_blocker/abort_handoff).
python scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py --release-final-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py --release-final-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_terminal_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.md

# P2-51: converge release final handoff to final closure contract (close_release/close_with_follow_up/close_blocker/abort_close).
python scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py --release-final-handoff-report .claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py --release-final-handoff-report .claude/reports/linux_unified_gate/ci_workflow_release_final_handoff.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_closure.md

# P2-52: publish release final closure contract (announce_release_closed/announce_release_closed_with_follow_up/announce_release_blocker/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py --release-final-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py --release-final-closure-report .claude/reports/linux_unified_gate/ci_workflow_release_final_closure.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.md

# P2-53: archive release final closure publish contract (archive_release_closed/archive_release_closed_with_follow_up/archive_release_blocker/abort_archive).
python scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py --release-final-closure-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py --release-final-closure-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_closure_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_archive.md

# P2-54: converge release final archive to final verdict contract (ship_release/ship_release_with_follow_up/escalate_release_blocker/abort_verdict).
python scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py --release-final-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py --release-final-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_final_archive.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.md

# P2-55: publish release final verdict contract (announce_release_shipped/announce_release_shipped_with_follow_up/announce_release_blocker/abort_publish).
python scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py --release-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py --release-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.md

# P2-56: archive release final verdict publish contract (archive_release_shipped/archive_release_shipped_with_follow_up/archive_release_blocker/abort_archive).
python scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py --release-final-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py --release-final-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_release_final_verdict_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.md

# P2-57: close gate-script/runtime-test/manifest drift contract.
python scripts/run_p2_linux_gate_manifest_drift_gate.py --dry-run --print-report
python scripts/run_p2_linux_gate_manifest_drift_gate.py --output-json .claude/reports/linux_unified_gate/linux_gate_manifest_drift.json --output-markdown .claude/reports/linux_unified_gate/linux_gate_manifest_drift.md

# P2-59: converge P2-56+P2-57 to one Linux terminal verdict contract.
python scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py --release-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json --gate-manifest-drift-report .claude/reports/linux_unified_gate/linux_gate_manifest_drift.json --dry-run --print-report
python scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py --release-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json --gate-manifest-drift-report .claude/reports/linux_unified_gate/linux_gate_manifest_drift.json --output-json .claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.md

# P2-60: dispatch Linux validation command from P2-59 terminal verdict contract.
python scripts/run_p2_lv_dispatch_gate.py --terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json --dry-run --print-report
python scripts/run_p2_lv_dispatch_gate.py --terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json --linux-validation-timeout-seconds 7200 --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.md

# P2-61: converge Linux validation dispatch into one final Linux validation verdict contract.
python scripts/run_p2_lv_verdict_gate.py --linux-validation-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json --dry-run --print-report
python scripts/run_p2_lv_verdict_gate.py --linux-validation-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.md

# P2-62: publish Linux validation verdict contract (announce_linux_validation_passed/announce_linux_validation_passed_with_follow_up/announce_linux_validation_blocker/abort_publish).
python scripts/run_p2_lv_verdict_publish_gate.py --linux-validation-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.json --dry-run --print-report
python scripts/run_p2_lv_verdict_publish_gate.py --linux-validation-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict_publish.md

# P2-63: terminal publish Linux validation verdict publish contract (announce_linux_validation_terminal_passed/announce_linux_validation_terminal_passed_with_follow_up/announce_linux_validation_terminal_blocker/abort_terminal_publish).
python scripts/run_p2_lv_terminal_publish_gate.py --linux-validation-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict_publish.json --dry-run --print-report
python scripts/run_p2_lv_terminal_publish_gate.py --linux-validation-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_verdict_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_publish.md

# P2-64: converge Linux validation terminal publish contract to final verdict (accept_linux_validation_terminal/accept_linux_validation_terminal_with_follow_up/escalate_linux_validation_terminal_blocker/abort_linux_validation_terminal_verdict).
python scripts/run_p2_lv_final_verdict_gate.py --linux-validation-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_publish.json --dry-run --print-report
python scripts/run_p2_lv_final_verdict_gate.py --linux-validation-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict.md

# P2-65: publish Linux validation final verdict contract (announce_linux_validation_final_validated/announce_linux_validation_final_validated_with_follow_up/announce_linux_validation_final_blocker/abort_publish).
python scripts/run_p2_lv_final_verdict_publish_gate.py --linux-validation-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict.json --dry-run --print-report
python scripts/run_p2_lv_final_verdict_publish_gate.py --linux-validation-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict_publish.md

# P2-66: archive Linux validation final verdict publish contract (archive_release_shipped/archive_release_shipped_with_follow_up/archive_release_blocker/abort_archive).
python scripts/run_p2_lv_final_publish_archive_gate.py --linux-validation-final-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict_publish.json --dry-run --print-report
python scripts/run_p2_lv_final_publish_archive_gate.py --linux-validation-final-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_verdict_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.md

# P2-67: converge Linux validation final publish archive contract to terminal verdict (proceed_linux_validation/proceed_linux_validation_with_follow_up/halt_linux_validation_blocker/abort_linux_validation).
python scripts/run_p2_lv_terminal_verdict_gate.py --linux-validation-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.json --dry-run --print-report
python scripts/run_p2_lv_terminal_verdict_gate.py --linux-validation-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_final_publish_archive.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.md

# P2-68: publish Linux validation terminal verdict contract (announce_linux_validation_terminal_ready/announce_linux_validation_terminal_ready_with_follow_up/announce_linux_validation_terminal_blocker/abort_publish).
python scripts/run_p2_lv_terminal_verdict_publish_gate.py --linux-validation-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.json --dry-run --print-report
python scripts/run_p2_lv_terminal_verdict_publish_gate.py --linux-validation-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict_publish.md

# P2-69: converge Linux validation terminal verdict publish to terminal dispatch contract (dispatch_linux_validation_terminal/dispatch_linux_validation_terminal_with_follow_up/hold_linux_validation_terminal_blocker/abort_linux_validation_terminal_dispatch).
python scripts/run_p2_lv_td_dispatch_gate.py --linux-validation-terminal-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict_publish.json --dry-run --print-report
python scripts/run_p2_lv_td_dispatch_gate.py --linux-validation-terminal-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_verdict_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.md

# P2-70: execute Linux validation terminal dispatch contract (dispatch_linux_validation_terminal/dispatch_linux_validation_terminal_with_follow_up/hold_linux_validation_terminal_blocker/abort_linux_validation_terminal_dispatch).
python scripts/run_p2_lv_td_execution_gate.py --linux-validation-terminal-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.json --dry-run --print-report
python scripts/run_p2_lv_td_execution_gate.py --linux-validation-terminal-dispatch-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch.json --linux-validation-terminal-timeout-seconds 7200 --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.md

# P2-71: trace Linux validation terminal dispatch execution run reference (run_tracking_ready/run_tracking_missing/run_poll_failed/run_in_progress/run_completed_success/run_completed_failure).
python scripts/run_p2_lv_td_trace_gate.py --linux-validation-terminal-dispatch-execution-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.json --dry-run --print-report
python scripts/run_p2_lv_td_trace_gate.py --linux-validation-terminal-dispatch-execution-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_execution.json --poll-timeout-seconds 600 --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.md

# P2-72: await Linux validation terminal dispatch completion (reuse P2-71 Linux validation terminal dispatch trace report).
python scripts/run_p2_lv_td_completion_gate.py --linux-validation-terminal-dispatch-trace-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.json --dry-run --print-report
python scripts/run_p2_lv_td_completion_gate.py --linux-validation-terminal-dispatch-trace-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_trace.json --poll-interval-seconds 20 --max-polls 15 --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.md

# P2-73: terminal publish Linux validation terminal dispatch completion contract (announce_linux_validation_terminal_dispatch_completed/announce_linux_validation_terminal_dispatch_completed_with_follow_up/announce_linux_validation_terminal_dispatch_in_progress/announce_linux_validation_terminal_dispatch_blocker/announce_linux_validation_terminal_dispatch_failed/abort_linux_validation_terminal_dispatch_terminal_publish).
python scripts/run_p2_lv_td_terminal_publish_gate.py --linux-validation-terminal-dispatch-completion-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.json --dry-run --print-report
python scripts/run_p2_lv_td_terminal_publish_gate.py --linux-validation-terminal-dispatch-completion-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_completion.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.md

# P2-74: final verdict Linux validation terminal dispatch terminal publish contract (accept_linux_validation_terminal_dispatch/accept_linux_validation_terminal_dispatch_with_follow_up/keep_linux_validation_terminal_dispatch_in_progress/escalate_linux_validation_terminal_dispatch_blocker/escalate_linux_validation_terminal_dispatch_failure/abort_linux_validation_terminal_dispatch_final_verdict).
python scripts/run_p2_lv_td_final_verdict_gate.py --linux-validation-terminal-dispatch-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json --dry-run --print-report
python scripts/run_p2_lv_td_final_verdict_gate.py --linux-validation-terminal-dispatch-terminal-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.md

# P2-75: publish Linux validation terminal dispatch final verdict contract (announce_linux_validation_terminal_dispatch_validated/announce_linux_validation_terminal_dispatch_validated_with_follow_up/announce_linux_validation_terminal_dispatch_in_progress/announce_linux_validation_terminal_dispatch_blocker/announce_linux_validation_terminal_dispatch_failure/abort_linux_validation_terminal_dispatch_final_verdict_publish).
python scripts/run_p2_lv_td_final_verdict_publish_gate.py --linux-validation-terminal-dispatch-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.json --dry-run --print-report
python scripts/run_p2_lv_td_final_verdict_publish_gate.py --linux-validation-terminal-dispatch-final-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict_publish.md

# P2-76: archive Linux validation terminal dispatch final verdict publish contract (archive_linux_validation_terminal_dispatch_validated/archive_linux_validation_terminal_dispatch_validated_with_follow_up/archive_linux_validation_terminal_dispatch_in_progress/archive_linux_validation_terminal_dispatch_blocker/archive_linux_validation_terminal_dispatch_failure/abort_linux_validation_terminal_dispatch_final_publish_archive).
python scripts/run_p2_lv_td_final_publish_archive_gate.py --linux-validation-terminal-dispatch-final-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict_publish.json --dry-run --print-report
python scripts/run_p2_lv_td_final_publish_archive_gate.py --linux-validation-terminal-dispatch-final-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_verdict_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.md

# P2-77: terminal verdict Linux validation terminal dispatch final publish archive contract (proceed_linux_validation_terminal_dispatch/proceed_linux_validation_terminal_dispatch_with_follow_up/hold_linux_validation_terminal_dispatch_in_progress/halt_linux_validation_terminal_dispatch_blocker/halt_linux_validation_terminal_dispatch_failure/abort_linux_validation_terminal_dispatch_terminal_verdict).
python scripts/run_p2_lv_td_terminal_verdict_gate.py --linux-validation-terminal-dispatch-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json --dry-run --print-report
python scripts/run_p2_lv_td_terminal_verdict_gate.py --linux-validation-terminal-dispatch-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.md

# P2-78: publish Linux validation terminal dispatch terminal verdict contract (announce_linux_validation_terminal_dispatch_ready/announce_linux_validation_terminal_dispatch_ready_with_follow_up/announce_linux_validation_terminal_dispatch_in_progress/announce_linux_validation_terminal_dispatch_blocker/announce_linux_validation_terminal_dispatch_failure/abort_linux_validation_terminal_dispatch_terminal_verdict_publish).
python scripts/run_p2_lv_td_tverdict_publish_gate.py --linux-validation-terminal-dispatch-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json --dry-run --print-report
python scripts/run_p2_lv_td_tverdict_publish_gate.py --linux-validation-terminal-dispatch-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.md

# P2-79: archive Linux validation terminal dispatch terminal verdict publish contract (archive_linux_validation_terminal_dispatch_ready/archive_linux_validation_terminal_dispatch_ready_with_follow_up/archive_linux_validation_terminal_dispatch_in_progress/archive_linux_validation_terminal_dispatch_blocker/archive_linux_validation_terminal_dispatch_failure/abort_linux_validation_terminal_dispatch_terminal_verdict_publish_archive).
python scripts/run_p2_lv_td_tverdict_publish_archive_gate.py --linux-validation-terminal-dispatch-terminal-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json --dry-run --print-report
python scripts/run_p2_lv_td_tverdict_publish_archive_gate.py --linux-validation-terminal-dispatch-terminal-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.md

# 涓€閿覆鑱?P2-17 -> P2-79 CI workflow 鍏ㄩ摼闂ㄧ锛圥2-26锛孡inux CI 鎬诲叆鍙ｏ級
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --dry-run
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --fail-fast --sync-write --command-guard-write --dispatch-trace-poll-now --completion-poll-interval-seconds 20 --completion-max-polls 15 --target-environment production --release-channel stable --release-workflow-path .github/workflows/release.yml --release-workflow-ref main --release-trace-poll-now --release-completion-poll-interval-seconds 20 --release-completion-max-polls 15 --on-release-hold pass --follow-up-repo acme/demo --follow-up-label release-follow-up
# 浠呮墽琛屽悗鍗婇摼锛堜粠娌荤悊鍙戝竷寮€濮嬶級
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance
# 浠呮墽琛?P2-29 缁堝眬鍙戝竷锛堝鐢ㄥ凡浜у嚭鐨?completion 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion
# 浠呮墽琛?P2-30 release handoff锛堝鐢ㄥ凡浜у嚭鐨?terminal publish 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --target-environment staging --release-channel canary --skip-release-trigger --skip-release-trace --skip-release-completion
# 浠呮墽琛?P2-31 release trigger锛堝鐢ㄥ凡浜у嚭鐨?release handoff 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --release-workflow-path .github/workflows/release.yml --release-workflow-ref main --skip-release-trace --skip-release-completion
# 浠呮墽琛?P2-32 release trace锛堝鐢ㄥ凡浜у嚭鐨?release trigger 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --release-trace-poll-now --skip-release-completion
# 浠呮墽琛?P2-33 release completion锛堝鐢ㄥ凡浜у嚭鐨?release trace 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --release-completion-poll-interval-seconds 20 --release-completion-max-polls 15 --skip-release-terminal-publish
# 浠呮墽琛?P2-34 release terminal publish锛堝鐢ㄥ凡浜у嚭鐨?release completion 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-finalization --skip-release-closure --skip-release-archive
# 浠呮墽琛?P2-35 release finalization锛堝鐢ㄥ凡浜у嚭鐨?release terminal publish 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --on-release-hold fail --skip-release-closure --skip-release-archive
# 浠呮墽琛?P2-36 release closure锛堝鐢ㄥ凡浜у嚭鐨?release finalization 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-archive
# 浠呮墽琛?P2-37 release archive锛堝鐢ㄥ凡浜у嚭鐨?release closure 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-verdict --skip-release-incident
# 浠呮墽琛?P2-38 release verdict锛堝鐢ㄥ凡浜у嚭鐨?release archive 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-incident
# 浠呮墽琛?P2-39 release incident锛堝鐢ㄥ凡浜у嚭鐨?release verdict 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-terminal-verdict --incident-repo acme/demo --incident-label release-incident
# 浠呮墽琛?P2-40 release terminal verdict锛堝鐢ㄥ凡浜у嚭鐨?release incident 鎶ュ憡锛?
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch
# P2-42 only: run release delivery terminal publish (reuse release delivery report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch
# P2-43 only: run release delivery final verdict (reuse release delivery terminal publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-follow-up-dispatch
# P2-44 only: run release follow-up dispatch (reuse release delivery final verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict
# P2-45 only: run release follow-up closure (reuse release follow-up dispatch report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --follow-up-repo acme/demo --follow-up-label release-follow-up

# P2-46 only: run release follow-up terminal publish (reuse release follow-up closure report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-final-verdict --follow-up-repo acme/demo --follow-up-label release-follow-up

# P2-47 only: run release follow-up final verdict (reuse release follow-up terminal publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --follow-up-repo acme/demo --follow-up-label release-follow-up
# P2-48 only: run release final outcome (reuse P2-43 + P2-47 final verdict reports).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict
# P2-49 only: run release final terminal publish (reuse P2-48 final outcome report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish
# P2-50 only: run release final handoff (reuse P2-49 final terminal publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-closure --skip-release-final-closure-publish
# P2-51 only: run release final closure (reuse P2-50 final handoff report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure-publish
# P2-52 only: run release final closure publish (reuse P2-51 final closure report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-archive

# P2-53 only: run release final archive (reuse P2-52 final closure publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish
# P2-54 only: run release final verdict (reuse P2-53 final archive report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive
# P2-55 only: run release final verdict publish (reuse P2-54 final verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict
# P2-56 only: run release final publish archive (reuse P2-55 final verdict publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish
# P2-57 only: run gate manifest drift closure (independent closure check over scripts/tests/manifest).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive
# P2-59 only: run terminal verdict closure (reuse P2-56 + P2-57 reports).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift
# P2-60 only: run Linux validation dispatch (reuse P2-59 terminal verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --linux-validation-timeout-seconds 7200
# P2-61 only: run Linux validation verdict (reuse P2-60 Linux validation dispatch report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch
# P2-62 only: run Linux validation verdict publish (reuse P2-61 Linux validation verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict
# P2-63 only: run Linux validation terminal publish (reuse P2-62 Linux validation verdict publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish
# P2-64 only: run Linux validation final verdict (reuse P2-63 Linux validation terminal publish report).
# P2-65 only: run Linux validation final verdict publish (reuse P2-64 Linux validation final verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict
# P2-66 only: run Linux validation final publish archive (reuse P2-65 Linux validation final verdict publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish
# P2-67 only: run Linux validation terminal verdict (reuse P2-66 Linux validation final publish archive report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive
# P2-68 only: run Linux validation terminal verdict publish (reuse P2-67 Linux validation terminal verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict
# P2-69 only: run Linux validation terminal dispatch (reuse P2-68 Linux validation terminal verdict publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict --skip-linux-validation-terminal-verdict-publish
# P2-70 only: run Linux validation terminal dispatch execution (reuse P2-69 Linux validation terminal dispatch report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict --skip-linux-validation-terminal-verdict-publish --skip-linux-validation-terminal-dispatch
# P2-71 only: run Linux validation terminal dispatch trace (reuse P2-70 Linux validation terminal dispatch execution report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict --skip-linux-validation-terminal-verdict-publish --skip-linux-validation-terminal-dispatch --skip-linux-validation-terminal-dispatch-execution --skip-linux-validation-terminal-dispatch-trace --skip-linux-validation-terminal-dispatch-completion
# P2-72 only: run Linux validation terminal dispatch completion (reuse P2-71 Linux validation terminal dispatch trace report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict --skip-linux-validation-terminal-verdict-publish --skip-linux-validation-terminal-dispatch --skip-linux-validation-terminal-dispatch-execution --skip-linux-validation-terminal-dispatch-trace --skip-linux-validation-terminal-dispatch-terminal-publish
# P2-73 only: run Linux validation terminal dispatch terminal publish (reuse P2-72 Linux validation terminal dispatch completion report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict --skip-linux-validation-terminal-verdict-publish --skip-linux-validation-terminal-dispatch --skip-linux-validation-terminal-dispatch-execution --skip-linux-validation-terminal-dispatch-trace --skip-linux-validation-terminal-dispatch-completion --skip-linux-validation-terminal-dispatch-final-verdict
# P2-74 only: run Linux validation terminal dispatch final verdict (reuse P2-73 Linux validation terminal dispatch terminal publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict --skip-linux-validation-terminal-verdict-publish --skip-linux-validation-terminal-dispatch --skip-linux-validation-terminal-dispatch-execution --skip-linux-validation-terminal-dispatch-trace --skip-linux-validation-terminal-dispatch-completion --skip-linux-validation-terminal-dispatch-terminal-publish
# P2-75 only: run Linux validation terminal dispatch final verdict publish (reuse P2-74 Linux validation terminal dispatch final verdict report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict --skip-linux-validation-terminal-verdict-publish --skip-linux-validation-terminal-dispatch --skip-linux-validation-terminal-dispatch-execution --skip-linux-validation-terminal-dispatch-trace --skip-linux-validation-terminal-dispatch-completion --skip-linux-validation-terminal-dispatch-terminal-publish --skip-linux-validation-terminal-dispatch-final-verdict --skip-linux-validation-terminal-dispatch-final-publish-archive
# P2-76 only: run Linux validation terminal dispatch final publish archive (reuse P2-75 Linux validation terminal dispatch final verdict publish report).
python scripts/run_p2_linux_ci_workflow_pipeline_gate.py --skip-plan --skip-yaml --skip-sync --skip-command-guard --skip-governance --skip-governance-publish --skip-decision --skip-dispatch --skip-dispatch-execution --skip-dispatch-trace --skip-dispatch-completion --skip-dispatch-terminal-publish --skip-dispatch-release-handoff --skip-release-trigger --skip-release-trace --skip-release-completion --skip-release-terminal-publish --skip-release-finalization --skip-release-closure --skip-release-archive --skip-release-verdict --skip-release-incident --skip-release-terminal-verdict --skip-release-delivery --skip-release-delivery-terminal-publish --skip-release-delivery-final-verdict --skip-release-follow-up-dispatch --skip-release-follow-up-closure --skip-release-follow-up-terminal-publish --skip-release-follow-up-final-verdict --skip-release-final-outcome --skip-release-final-terminal-publish --skip-release-final-handoff --skip-release-final-closure --skip-release-final-closure-publish --skip-release-final-archive --skip-release-final-verdict --skip-release-final-verdict-publish --skip-release-final-publish-archive --skip-gate-manifest-drift --skip-terminal-verdict --skip-linux-validation-dispatch --skip-linux-validation-verdict --skip-linux-validation-verdict-publish --skip-linux-validation-terminal-publish --skip-linux-validation-final-verdict --skip-linux-validation-final-verdict-publish --skip-linux-validation-final-publish-archive --skip-linux-validation-terminal-verdict --skip-linux-validation-terminal-verdict-publish --skip-linux-validation-terminal-dispatch --skip-linux-validation-terminal-dispatch-execution --skip-linux-validation-terminal-dispatch-trace --skip-linux-validation-terminal-dispatch-completion --skip-linux-validation-terminal-dispatch-terminal-publish --skip-linux-validation-terminal-dispatch-final-verdict --skip-linux-validation-terminal-dispatch-terminal-verdict
# P2-77 only: run Linux validation terminal dispatch terminal verdict (reuse P2-76 Linux validation terminal dispatch final publish archive report).
python scripts/run_p2_lv_td_terminal_verdict_gate.py --linux-validation-terminal-dispatch-final-publish-archive-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_final_publish_archive.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.md
# P2-78 only: run Linux validation terminal dispatch terminal verdict publish (reuse P2-77 Linux validation terminal dispatch terminal verdict report).
python scripts/run_p2_lv_td_tverdict_publish_gate.py --linux-validation-terminal-dispatch-terminal-verdict-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.md
# P2-79 only: run Linux validation terminal dispatch terminal verdict publish archive (reuse P2-78 Linux validation terminal dispatch terminal verdict publish report).
python scripts/run_p2_lv_td_tverdict_publish_archive_gate.py --linux-validation-terminal-dispatch-terminal-verdict-publish-report .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish.json --output-json .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.json --output-markdown .claude/reports/linux_unified_gate/ci_workflow_linux_validation_terminal_dispatch_terminal_verdict_publish_archive.md

# 璇硶妫€鏌?
python scripts/check_syntax.py --root claude_code

# 杩愯鎬ц兘 smoke
python -m pytest -q -c pytest.ini tests/perf/test_perf_smoke.py

# 鐢熸垚鎬ц兘鍩虹嚎
python scripts/perf/run_baseline.py --project-root . --iterations 20 --output docs/current/performance/baseline_v1.json
```

鏈鏁寸悊鏃跺疄闄呭鏍歌繃锛?

```bash
python -m pytest -q -c pytest.ini
```

缁撴灉涓?`90 passed`銆?

## 閰嶇疆涓庤繍琛屾椂鏂囦欢

褰撳墠浠ｇ爜閲屽父瑙佺殑閰嶇疆涓庤繍琛屾椂鏂囦欢鍒嗗竷濡備笅锛?

| 浣嶇疆 | 鐢ㄩ€?|
|---|---|
| `~/.claude-code-python/base.json` | 鍏ㄥ眬鍩虹閰嶇疆 |
| `~/.claude-code-python/{env}.json` | 鎸夌幆澧冨垎灞傞厤缃?|
| `~/.claude-code-python/config.json` | 鐢ㄦ埛鎵嬪伐瑕嗙洊閰嶇疆 |
| `.claude-code-python.json` | 椤圭洰鏈湴璁剧疆 |
| `.claude/` | 椤圭洰杩愯鏁版嵁鐩綍锛屽父瑙佸唴瀹瑰寘鎷换鍔°€佽鍒掋€佹妧鑳姐€乭ooks銆乼odo銆乼eam銆乻cheduled tasks |
| `.mcp.json` | MCP 鐩稿叧閰嶇疆 |
| `CLAUDE.md` / `CLAUDE.local.md` | 椤圭洰鎸囧淇℃伅锛岀敱 `/init` 鍒濆鍖?|

濡傛灉浣犺鎺掓煡浠诲姟绯荤粺锛屼紭鍏堝叧娉細

- `.claude/tasks.json`
- `.claude/runtime_tasks.json`
- `.claude/scheduled_tasks.json`

## 绀轰緥涓庡叆鍙ｆ枃浠?

- `examples/basic_usage.py`锛氬熀纭€璋冪敤绀轰緥
- `examples/configuration.py`锛氶厤缃ず渚?
- `examples/custom_tools.py`锛氳嚜瀹氫箟宸ュ叿绀轰緥
- `examples/mcp_integration.py`锛歁CP 闆嗘垚绀轰緥
- `examples/session_management.py`锛氫細璇濈鐞嗙ず渚?

## 鍚庣画鏂囨。缁存姢瑙勫垯

涓轰簡閬垮厤鏂囨。鍐嶆鑶ㄨ儉锛屽悗缁缓璁伒瀹堜互涓嬭鍒欙細

1. README 鍙仛鍏ュ彛銆佹憳瑕佸拰瀵艰埅锛屼笉鍐嶈拷鍔犲ぇ鍨嬩笓棰樿鏄庛€?
2. 鍚屼竴涓婚鏈€澶氫繚鐣欎竴涓€滃綋鍓嶄富鏂囨。鈥濆拰涓€涓€滃巻鍙茶ˉ鍏呮枃妗ｂ€濄€?
3. 鏂扮殑璇勪及/鎬荤粨鏂囨。蹇呴』甯︽棩鏈燂紝骞舵槑纭嚜宸辨槸鍚﹀彇浠ｆ棫鏂囨。銆?
4. 瓒呰繃涓€椤电殑涓撻鍐呭鐩存帴鏀惧埌 `docs/`锛孯EADME 鍙啓鎽樿鍜岄摼鎺ャ€?
5. 濡傛灉鏌愪釜涓撻宸茬粡鏈変富鏂囨。锛屽悗缁ˉ鍏呬紭鍏堟洿鏂板師鏂囨。锛岃€屼笉鏄柊寤哄钩琛屾枃妗ｃ€?

## 缁撹

杩欐鏁寸悊鍚庯紝`README.md` 涓嶅啀鎵挎媴鈥滄墍鏈夌煡璇嗛兘鍐欏湪涓€澶勨€濈殑鑱岃矗锛岃€屾槸鎴愪负浠撳簱鐨勭ǔ瀹氬叆鍙ｏ細

- 鎯宠繍琛岄」鐩紝鍏堢湅鈥滃揩閫熷紑濮嬧€?
- 鎯崇湅褰撳墠鏋舵瀯/鎬ц兘/涓棿浠剁姸鎬侊紝鐩存帴鐪嬪搴斾富鏂囨。
- 鎯虫繁鍏?Agent 鎴?MCP锛屽啀杩涘叆澶ф枃妗?
- 鎯宠拷婧巻鍙查棶棰樺拰淇鏂规锛屽啀鐪嬪巻鍙叉枃妗?

杩欏氨鏄綋鍓嶄粨搴撴枃妗ｇ殑鎺ㄨ崘闃呰椤哄簭鍜岀淮鎶よ竟鐣屻€?






