# Claude Code Python 鎵ц璁″垝涓庝换鍔″崱鍗曪紙2026-04-29锛?
## 1. 鏂囨。瀹氫綅

- 鏂囨。鎬ц川锛氭墽琛岃鍒?+ 浠诲姟鍗″崟
- 涓婃父鏂囨。锛歔CLAUDE_CODE_SUPERSEDE_STRATEGY_2026-04-29.md](D:/Download/gaming/new_program/claude-code-python/docs/current/architecture/CLAUDE_CODE_SUPERSEDE_STRATEGY_2026-04-29.md)
- 浣跨敤鏂瑰紡锛?  - 浜у搧銆佹灦鏋勩€佺爺鍙戙€佹祴璇曢兘浠ユ湰鏂囦欢浣滀负杩戞湡瀹炴柦娓呭崟
  - 姣忓紶浠诲姟鍗″繀椤昏兘鐙珛寤哄垎鏀€佺嫭绔嬪紑鍙戙€佺嫭绔嬮獙璇併€佺嫭绔嬪悎骞?  - 鑻ヤ竴寮犲崱鏃犳硶鍦ㄤ竴涓槑纭竟鐣屽唴瀹屾垚锛屽垯缁х画鍚戜笅鎷?
## 2. 褰撳墠鎷嗚В鍘熷垯

### 2.1 鎷嗗崱鍘熷垯

姣忓紶鍗″繀椤诲悓鏃跺洖绛?5 涓棶棰橈細

1. 瑙ｅ喅浠€涔堥棶棰橈紵
2. 瑕佸仛浠€涔堢爺鍙戝姛鑳斤紵
3. 瑕佸仛鍒颁粈涔堢▼搴︽墠绠楀畬鎴愶紵
4. 娴嬭瘯浠ｇ爜瑕佽ˉ鍒颁粈涔堢▼搴︼紵
5. 鏈変粈涔堝墠缃緷璧栧拰鏄庣‘闈炵洰鏍囷紵

### 2.2 瀹屾垚瀹氫箟锛圖efinition of Done锛?
姣忓紶鍗￠粯璁ゅ畬鎴愭爣鍑嗭細

- 浠ｇ爜涓婚摼鍙繍琛?- 鏂板鎴栦慨鏀规祴璇曢€氳繃
- 瀵瑰簲鏂囨。鍚屾鏇存柊
- 涓嶅紩鍏ユ柊鐨勬湭瑙ｉ噴鑴忕姸鎬?- 鑷冲皯瀹屾垚涓€杞湰鍦版墜宸ラ獙鏀?
### 2.3 娴嬭瘯鍒嗗眰鏍囧噯

涓洪伩鍏嶁€滃啓浜嗙偣娴嬭瘯鈥濅絾娌℃湁楠屾敹浠峰€硷紝缁熶竴閲囩敤浠ヤ笅娣卞害鍒嗗眰锛?
| 灞傜骇 | 鍚嶇О | 鐩殑 | 鏈€浣庤姹?|
|---|---|---|---|
| T1 | Unit | 绾嚱鏁般€佺姸鎬佹満銆佽緭鍏ヨ緭鍑鸿竟鐣?| 姝ｅ悜 + 璐熷悜 + 杈圭晫 |
| T2 | Component | 鍗曟ā鍧楃紪鎺掋€佸甫 fake/mocks 鐨勮涓洪獙璇?| 鑷冲皯瑕嗙洊 1 鏉′富閾?+ 1 鏉″紓甯搁摼 |
| T3 | Integration | 璺ㄦā鍧楄仈鍔紝楠岃瘉鐪熷疄渚濊禆杈圭晫 | 鑷冲皯瑕嗙洊 1 鏉＄鍒扮涓氬姟閾?|
| T4 | Regression | 澶嶇幇鍘嗗彶缂洪櫡锛岄槻姝㈠洖褰?| 姣忎釜宸茬煡 bug 鑷冲皯 1 鏉″洖褰掔敤渚?|
| T5 | Manual Smoke | 浜哄伐蹇€熼獙鏀?| 鍛戒护绾?鍏ュ彛绾у疄闄呰繍琛?|

### 2.4 娴嬭瘯浜х墿瑕佹眰

姣忓紶浠ｇ爜鍗¤嚦灏戞弧瓒筹細

- 鏂板鎴栦慨鏀?`T1/T2` 娴嬭瘯
- 鑻ュ彉鏇村奖鍝?CLI銆乻ession銆乼ask銆丮CP銆乭ooks銆乤gent 涓婚摼锛屽垯蹇呴』琛?`T3`
- 鑻ヤ换鍔″崱婧愪簬宸茬煡缂洪櫡锛屽垯蹇呴』琛?`T4`
- 杈撳嚭 1 浠芥渶灏忔墜宸ラ獙鏀跺懡浠ゆ竻鍗?
## 3. 瀹炴柦闃舵鎬昏

## 3.1 Phase 0锛氭琛€涓庢敹鏁?
鐩爣锛?
- 淇帀鈥滅湅璧锋潵鏈夈€佸疄闄呮病鎵撻€氣€濈殑鍋囬棴鐜?- 寤虹珛鍞竴涓昏繍琛屾椂鍏ュ彛
- 寤虹珛绋冲畾鐨勬湰鍦板紑鍙?娴嬭瘯鏂藉伐闈?
## 3.2 Phase 1锛氬钩鍙板寲

鐩爣锛?
- 浠庡崟杩涚▼ CLI 婕旇繘涓哄彲澶嶇敤鐨勬墽琛屽悗绔?- 琛ラ綈 event journal銆乻tate backend銆乤ctive memory

## 3.3 Phase 2锛氳秴杞?
鐩爣锛?
- 寤虹珛澶?Agent 鎺у埗闈€両DE 瀹㈡埛绔€丆I 宸ヤ綔娴併€佺粍缁囩骇娌荤悊鑳藉姏

## 4. 渚濊禆椤哄簭鍥?
```text
P0-01 Runtime Backbone
  -> P0-02 Session Resume
  -> P0-03 Auth/Config
  -> P0-04 Feature Flags
  -> P0-05 Review Command
  -> P0-06 Session/History/Memory Boundaries
  -> P0-07 Hooks Runtime
  -> P0-08 Windows Bootstrap
  -> P0-09 Temp Artifact Hygiene
  -> P0-10 Phase0 Regression Gate

P1-01 Daemon/API Control Plane
  -> P1-02 Event Journal
  -> P1-03 SQLite State Backend
  -> P1-04 Active Memory Runtime
  -> P1-05 Hook Policy/Audit Convergence
  -> P1-06 CLI Thin Client Migration

P2-01 Agent Supervisor
  -> P2-02 Artifact Bus
  -> P2-03 IDE Integration
  -> P2-04 GitHub/CI Workflow
  -> P2-05 Org Policy & Audit
  -> P2-06 Linux Unified Verification Gate
  -> P2-07 Agent Runtime Parity
  -> P2-08 Custom Agents Directory Loader
  -> P2-09 Linux Unified Execution Gate
  -> P2-10 JetBrains IDE Integration
  -> P2-11 Linux Sharded Execution Gate
  -> P2-12 Linux Shard Aggregation Gate
  -> P2-13 Linux Final Report Publish Gate
  -> P2-14 Linux Unified Pipeline Orchestration Gate
  -> P2-15 Linux Shard Plan Generation Gate
  -> P2-16 Linux CI Matrix Export Gate
  -> P2-17 Linux CI Workflow Plan Gate
  -> P2-18 Linux CI Workflow YAML Render Gate
  -> P2-19 Linux CI Workflow Drift Sync Gate
  -> P2-20 Linux CI Workflow Command Guard Gate
  -> P2-21 Linux CI Workflow Governance Convergence Gate
  -> P2-22 Linux CI Workflow Governance Publish Gate
  -> P2-23 Linux CI Workflow Execution Decision Gate
  -> P2-24 Linux CI Workflow Dispatch Readiness Gate
  -> P2-25 Linux CI Workflow Dispatch Execution Gate
  -> P2-26 Linux CI Workflow Full Pipeline Gate
  -> P2-27 Linux CI Workflow Dispatch Traceability Gate
  -> P2-28 Linux CI Workflow Dispatch Completion Gate
  -> P2-29 Linux CI Workflow Terminal Publish Gate
  -> P2-30 Linux CI Workflow Release Handoff Gate
  -> P2-31 Linux CI Workflow Release Trigger Gate
  -> P2-32 Linux CI Workflow Release Traceability Gate
  -> P2-33 Linux CI Workflow Release Completion Gate
  -> P2-34 Linux CI Workflow Release Terminal Publish Gate
  -> P2-35 Linux CI Workflow Release Finalization Gate
  -> P2-36 Linux CI Workflow Release Closure Publish Gate
  -> P2-37 Linux CI Workflow Release Archive Publish Gate
  -> P2-38 Linux CI Workflow Release Verdict Publish Gate
  -> P2-39 Linux CI Workflow Release Incident Dispatch Gate
  -> P2-40 Linux CI Workflow Release Terminal Verdict Publish Gate
  -> P2-41 Linux CI Workflow Release Delivery Closure Gate
  -> P2-42 Linux CI Workflow Release Delivery Terminal Publish Gate
  -> P2-43 Linux CI Workflow Release Delivery Final Verdict Gate
  -> P2-44 Linux CI Workflow Release Follow-Up Dispatch Gate
  -> P2-45 Linux CI Workflow Release Follow-Up Closure Gate
  -> P2-46 Linux CI Workflow Release Follow-Up Terminal Publish Gate
  -> P2-47 Linux CI Workflow Release Follow-Up Final Verdict Gate
  -> P2-48 Linux CI Workflow Release Final Outcome Gate
  -> P2-49 Linux CI Workflow Release Final Terminal Publish Gate
  -> P2-50 Linux CI Workflow Release Final Handoff Gate
  -> P2-51 Linux CI Workflow Release Final Closure Gate
  -> P2-52 Linux CI Workflow Release Final Closure Publish Gate
  -> P2-53 Linux CI Workflow Release Final Archive Gate
  -> P2-54 Linux CI Workflow Release Final Verdict Gate
  -> P2-55 Linux CI Workflow Release Final Verdict Publish Gate
  -> P2-56 Linux CI Workflow Release Final Publish Archive Gate
  -> P2-57 Linux Gate Manifest Drift Closure Gate
  -> P2-59 Linux CI Workflow Terminal Verdict Closure Gate
  -> P2-60 Linux CI Workflow Linux Validation Dispatch Gate
  -> P2-61 Linux CI Workflow Linux Validation Verdict Gate
```

## 5. Phase 0 浠诲姟鍗″崟

## P0-01 缁熶竴涓昏繍琛屾椂楠ㄦ灦

- 鍗″彿锛歚P0-01`
- 浼樺厛绾э細`P0`
- 瑙ｅ喅闂锛?  - `main.py`銆乣app.py`銆乻ession/task/hooks/memory 鍒濆鍖栭摼鏉″垎鏁?  - 瀛愮郴缁熷瓨鍦ㄤ絾鏈舰鎴愬敮涓€杩愯鏃堕棴鐜?- 鐮斿彂鍔熻兘锛?  - 寤虹珛缁熶竴 runtime bootstrap
  - 鏄庣‘ `main -> Application -> QueryEngine -> Session -> TaskManager -> Hooks -> Memory`
  - 娑堥櫎閲嶅鍒濆鍖栬矾寰勪笌闅愬紡鍏ㄥ眬鐘舵€佷緷璧?- 瀹炴柦鑼冨洿锛?  - `claude_code/main.py`
  - `claude_code/app.py`
  - `claude_code/engine/query.py`
  - 瑙嗛渶瑕佹柊澧?`claude_code/runtime/` 鎴栫瓑浠锋ā鍧?- 瀹屾垚绋嬪害锛?  - REPL銆乻ingle query銆乸ipe銆丮CP serve 鍏辩敤鍚屼竴 bootstrap 娴?  - runtime 鍏抽敭瀵硅薄鏈夊敮涓€鏋勫缓璺緞
  - 鍚庣画鍗″崟涓嶅啀渚濊禆鈥滃悇鑷伔鍋峰垵濮嬪寲鈥?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歜ootstrap 鍙傛暟瑙ｆ瀽銆乺untime object 鏋勫缓杈圭晫
  - `T2`锛氫笉鍚岃繍琛屾ā寮忎笅 runtime 缁勪欢瑁呴厤涓€鑷存€?  - `T3`锛歊EPL / pipe / single query 鑷冲皯鍚勬湁 1 鏉′富閾?smoke
  - `T4`锛氳鐩栤€滄煇妯″紡婕忓垵濮嬪寲鏌愭湇鍔♀€濈殑鍘嗗彶鏂偣
- 寤鸿娴嬭瘯鏂囦欢锛?  - 鏂板 `tests/test_runtime_bootstrap.py`
  - 鎵╁睍 `tests/test_main_runtime.py`
- 鎵嬪伐楠屾敹锛?  - `python -m claude_code.main --help`
  - `python -m claude_code.main --doctor`
  - `echo hi | python -m claude_code.main --pipe`
- 闈炵洰鏍囷細
  - 鏈崱涓嶅紩鍏?daemon/API
  - 鏈崱涓嶅鐞嗙粍缁囩骇绛栫暐
- 鍓嶇疆渚濊禆锛氭棤

## P0-02 /resume 鐪熼棴鐜?
- 鍗″彿锛歚P0-02`
- 浼樺厛绾э細`P0`
- 瑙ｅ喅闂锛?  - `QueryEngine.resume_session()` 宸插瓨鍦紝浣?`/resume` 鍛戒护娌℃湁鐪熸璋冪敤鎭㈠閾捐矾
  - session 鎭㈠鏄€滄枃妗堝姛鑳解€濓紝涓嶆槸鈥滆繍琛屾椂鍔熻兘鈥?- 鐮斿彂鍔熻兘锛?  - 灏?`/resume [session_id]` 鐪熸鎺ュ叆 `QueryEngine.resume_session()`
  - 鏃犲弬鏁版椂鍒楁渶杩?session锛涙湁鍙傛暟鏃舵仮澶嶆寚瀹?session 骞舵帴缁璇?  - 鏄庣‘鎭㈠鍚庣殑 session id銆乵essage list銆亀orking directory 琛屼负
- 瀹炴柦鑼冨洿锛?  - `claude_code/commands/compact/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/engine/session.py`
  - `claude_code/repl/__init__.py`
- 瀹屾垚绋嬪害锛?  - `/resume` 涓嶅啀鍙繑鍥炶鏄庢枃瀛?  - 鎭㈠鍚庝笅涓€杞?query 鑳芥帴鐫€鍘嗗彶娑堟伅杩愯
  - 鎭㈠澶辫触鏃舵湁鍙瘖鏂敊璇俊鎭?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歴ession list / load 杈圭晫
  - `T2`锛歝ommand -> engine 鎭㈠閾捐矾
  - `T3`锛氬垱寤?session銆佹寔涔呭寲銆佹仮澶嶃€佺户缁棶绛旂殑涓€鏉″畬鏁撮摼
  - `T4`锛氭棤 session / session_id 涓嶅瓨鍦?/ 浼氳瘽鏂囦欢鎹熷潖
- 寤鸿娴嬭瘯鏂囦欢锛?  - 鎵╁睍 `tests/test_query_engine_runtime.py`
  - 鎵╁睍 `tests/test_main_runtime.py`
  - 鏂板 `tests/test_resume_runtime.py`
- 鎵嬪伐楠屾敹锛?  - 鍚姩涓€娆′細璇濆苟鐢熸垚鎸佷箙鍖?  - 鏂拌繘绋嬫墽琛?`/resume`
  - 纭鎭㈠鍚庣户缁璇?- 闈炵洰鏍囷細
  - 涓嶅紩鍏ヨ法鏈哄櫒鎭㈠
  - 涓嶅紩鍏?session 鎼滅储 UI
- 鍓嶇疆渚濊禆锛歚P0-01`

## P0-03 auth/config 涓婚摼淇涓庣粺涓€

- 鍗″彿锛歚P0-03`
- 浼樺厛绾э細`P0`
- 瑙ｅ喅闂锛?  - `logout` / `auth` 浣跨敤鏈鍏ョ殑 `ConfigManager`
  - `Config` 涓?`ConfigManager` 鍙岃建骞跺瓨锛岃璇佺姸鎬佸垽瀹氫笉绋冲畾
- 鐮斿彂鍔熻兘锛?  - 閫夊畾 canonical config 璇诲啓璺緞
  - 淇 `/login`銆乣/logout`銆乣/auth`
  - 缁熶竴 env/config/key masking 瑙勫垯
- 瀹炴柦鑼冨洿锛?  - `claude_code/commands/auth/__init__.py`
  - `claude_code/config.py`
  - `claude_code/utils/config_manager.py`
  - 瑙嗛渶瑕佽皟鏁?`claude_code/main.py`
- 瀹屾垚绋嬪害锛?  - `auth` 閾捐矾鏃?`NameError`
  - 璁よ瘉鐘舵€佽緭鍑轰笌瀹為檯 env/config 涓€鑷?  - logout 鑳芥竻鐞?runtime 鍙鐨?key 鏉ユ簮
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歟nv > config > default 浼樺厛绾?  - `T2`锛歛uth commands 鍦ㄤ笉鍚?key 鏉ユ簮涓嬬殑琛屼负
  - `T3`锛氬懡浠ょ骇鐘舵€佸彉鍖栭獙璇?  - `T4`锛氭棤 key / config 缂哄け / key mask 杈撳嚭
- 寤鸿娴嬭瘯鏂囦欢锛?  - 鏂板 `tests/test_commands_auth_runtime.py`
  - 鎵╁睍 `tests/test_main_runtime.py`
- 鎵嬪伐楠屾敹锛?  - 璁剧疆 env key
  - 杩愯 `/auth`
  - 杩愯 `/logout`
  - 鍐嶆杩愯 `/auth`
- 闈炵洰鏍囷細
  - 涓嶅紩鍏?OAuth 鐪熺櫥褰曟祦
  - 涓嶆帴绗笁鏂?secrets manager
- 鍓嶇疆渚濊禆锛歚P0-01`

## P0-04 feature flag 杩愯鏃朵慨澶?
- 鍗″彿锛歚P0-04`
- 浼樺厛绾э細`P0`
- 瑙ｅ喅闂锛?  - `FeatureConfig` 涓?frozen dataclass锛屼絾 `enable()/disable()` 璇曞浘鍘熷湴淇敼
  - 褰撳墠 flag 鏈哄埗瀵规湭鏉ュぇ鍔熻兘鍒囨崲涓嶅彲闈?- 鐮斿彂鍔熻兘锛?  - 閲嶆瀯 feature registry 鐨勫唴閮ㄧ姸鎬佽〃杈?  - 淇濇寔 env fallback锛屽悓鏃跺厑璁哥▼搴忓唴瀹夊叏鍒囨崲
  - 鏄庣‘ feature 璇诲彇涓庡啓鍏ヨ涔?- 瀹炴柦鑼冨洿锛?  - `claude_code/features.py`
- 瀹屾垚绋嬪害锛?  - `enable()` / `disable()` 涓嶆姏 `FrozenInstanceError`
  - registry 鍐呭琛屼负涓€鑷?  - flags 鍙綔涓哄悗缁ぇ鍗＄殑 gated rollout 鏈哄埗
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歟nable / disable / env override / unknown feature
  - `T2`锛歳egistry 瀹炰緥鍦ㄥ娆¤皟鐢ㄤ腑鐨勭姸鎬佷竴鑷存€?  - `T4`锛氬鐜板綋鍓?`FrozenInstanceError` 鐨勫洖褰掔敤渚?- 寤鸿娴嬭瘯鏂囦欢锛?  - 鏂板 `tests/test_features_runtime.py`
- 鎵嬪伐楠屾敹锛?  - 鏈湴鑴氭湰鍒囨崲 feature 骞惰鍙?- 闈炵洰鏍囷細
  - 涓嶅紩鍏ヨ繙绋?flag service
- 鍓嶇疆渚濊禆锛氭棤

## P0-05 review 鍛戒护浜у搧鍖?
- 鍗″彿锛歚P0-05`
- 浼樺厛绾э細`P0`
- 瑙ｅ喅闂锛?  - `/review` 鍙槸寮曞鏂囨锛屼笉鎵ц鐪熷疄瀹℃煡
  - 鐢ㄦ埛鏃犳硶渚濊禆璇ュ懡浠ゆ鏌?diff / 鏂囦欢椋庨櫓
- 鐮斿彂鍔熻兘锛?  - 鏀寔 review 褰撳墠 git diff
  - 鏀寔 review 鎸囧畾鏂囦欢
  - 缁熶竴 findings 杈撳嚭鏍煎紡锛氶棶棰樸€佷綅缃€佷弗閲嶅害銆佸缓璁?  - 鏄庣‘鈥滄棤鍙戠幇鈥濊緭鍑?- 瀹炴柦鑼冨洿锛?  - `claude_code/commands/review/__init__.py`
  - 瑙嗛渶瑕佹柊澧?`claude_code/services/review_service.py`
  - 鍙帴鍏?`git diff` / read-only analyzer
- 瀹屾垚绋嬪害锛?  - `/review` 涓嶅啀杩斿洖鍗犱綅 prompt
  - 鑳藉褰撳墠鏀瑰姩鎴栬緭鍏ユ枃浠剁粰鍑虹粨鏋勫寲缁撴灉
  - 杈撳嚭鍙綔涓哄悗缁?PR/CI review 鐨勯洀褰?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氬弬鏁拌В鏋愩€佹棤杈撳叆榛樿琛屼负
  - `T2`锛歴ervice 瀵?fake diff 鐨?findings 鐢熸垚
  - `T3`锛氫复鏃?git repo 涓殑 review 涓婚摼
  - `T4`锛氭棤 diff / 鏂囦欢涓嶅瓨鍦?/ 绌虹粨鏋?- 寤鸿娴嬭瘯鏂囦欢锛?  - 鏂板 `tests/test_review_command_runtime.py`
- 鎵嬪伐楠屾敹锛?  - 淇敼涓€涓枃浠跺悗鎵ц `/review`
  - 鎸囧畾鏂囦欢鎵ц `/review path`
- 闈炵洰鏍囷細
  - 涓嶅仛缁勭粐绾?code review dashboard
  - 涓嶅己琛屾帴 GitHub API
- 鍓嶇疆渚濊禆锛歚P0-01`

## P0-06 session/history/memory 鑱岃矗鏀舵暃

- 鍗″彿锛歚P0-06`
- 浼樺厛绾э細`P0`
- 瑙ｅ喅闂锛?  - `Session`銆乣HistoryManager`銆乣SessionMemory` 鑱岃矗浜ゅ弶
  - 鐭湡瀵硅瘽銆侀暱鏈熻蹇嗐€佸綊妗ｅ巻鍙茶竟鐣屼笉娓?- 鐮斿彂鍔熻兘锛?  - 鏄庣‘涓夊眰鑱岃矗锛?    - `Session`锛氬綋鍓嶄細璇濅簨瀹?    - `History`锛氬凡缁撴潫/宸蹭繚瀛樼殑娑堟伅褰掓。
    - `Memory`锛氶暱鏈熺粨鏋勫寲鐭ヨ瘑
  - 娑堥櫎閲嶅淇濆瓨涓庝笉涓€鑷村姞杞借矾寰?  - 涓?P1 active memory 閾哄簳
- 瀹炴柦鑼冨洿锛?  - `claude_code/engine/session.py`
  - `claude_code/services/history_manager.py`
  - `claude_code/services/memory_service.py`
  - `claude_code/context/builder.py`
- 瀹屾垚绋嬪害锛?  - 涓夎€呰亴璐ｄ笌璋冪敤杈圭晫鍐欐竻
  - 褰撳墠涓婚摼鍙繚鐣欎竴涓?message persistence source of truth
  - memory 涓嶅啀闅愬紡鎵挎媴 session/history 瑙掕壊
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歴ave/load/export/search 杈圭晫
  - `T2`锛歴ession -> persisted session 琛屼负
  - `T3`锛歝ontext builder 璇诲彇 memory/session 鐨勮仈鍔?  - `T4`锛氶槻姝㈤噸澶嶆秷鎭€侀噸澶嶆寔涔呭寲銆侀敊璇仮澶?- 寤鸿娴嬭瘯鏂囦欢锛?  - 鏂板 `tests/test_session_history_memory_runtime.py`
  - 鎵╁睍 `tests/test_context_builder_runtime.py`
- 鎵嬪伐楠屾敹锛?  - 鐢熸垚浼氳瘽
  - 閲嶅惎鍔犺浇
  - 楠岃瘉 memory 涓嶈璇啓涓鸿亰澶╁巻鍙?- 闈炵洰鏍囷細
  - 涓嶅仛鍚戦噺鏁版嵁搴?  - 涓嶅仛闀挎湡妫€绱㈠寮?- 鍓嶇疆渚濊禆锛歚P0-01`

## P0-07 hooks 鎺ュ叆涓昏繍琛屾椂

- 鍗″彿锛歚P0-07`
- 浼樺厛绾э細`P0`
- 瑙ｅ喅闂锛?  - hooks command銆乭ooks manager銆乼ool/command 鎵ц閾炬病鏈夌湡姝ｈ仈鍔?  - hooks 鐩墠鏇村儚闈欐€侀厤缃紝鑰屼笉鏄繍琛屾椂鑳藉姏
- 鐮斿彂鍔熻兘锛?  - 鍦?tool execution 鍓嶅悗瑙﹀彂 hooks
  - 鍦?command 鎵ц鍓嶅悗瑙﹀彂 hooks
  - 鍦ㄩ敊璇矾寰勮Е鍙?`on_error`
  - 绾﹀畾 hook context payload
- 瀹炴柦鑼冨洿锛?  - `claude_code/services/hooks_manager.py`
  - `claude_code/commands/hooks/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/repl/__init__.py`
  - 瑙嗛渶瑕佹帴鍏?command dispatch 灞?- 瀹屾垚绋嬪害锛?  - hooks 閰嶇疆鑳界湡瀹炵敓鏁?  - disabled hook銆佽秴鏃?hook銆佸け璐?hook 琛屼负娓呮櫚
  - 瀵逛富閾惧け璐ヤ笉浜х敓涓嶅彲鎺у壇浣滅敤
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歨ook load/save/parse
  - `T2`锛歵rigger before_tool / after_tool / on_error
  - `T3`锛氱湡瀹?tool 璋冪敤閾捐Е鍙?hook
  - `T4`锛歨ook timeout / hook command failure / disabled hook
- 寤鸿娴嬭瘯鏂囦欢锛?  - 鏂板 `tests/test_hooks_runtime.py`
- 鎵嬪伐楠屾敹锛?  - 閰嶇疆涓€涓畝鍗?echo hook
  - 鎵ц read / grep / bash
  - 纭 hook 琚Е鍙?- 闈炵洰鏍囷細
  - 涓嶅仛 org-wide hook registry
- 鍓嶇疆渚濊禆锛歚P0-01`

## P0-08 Windows 鍚姩涓庤В閲婂櫒鎺㈡祴绋冲畾鍖?
- 鍗″彿锛歚P0-08`
- 浼樺厛绾э細`P1`
- 瑙ｅ喅闂锛?  - 绯荤粺 `python` 鎸囧悜 WindowsApps stub锛岀敤鎴峰鏄撹窇鍒板亣瑙ｉ噴鍣?  - Windows 鐢ㄦ埛鍚姩閾捐剢寮?- 鐮斿彂鍔熻兘锛?  - 鍦?`--doctor` 涓瘑鍒В閲婂櫒鏉ユ簮
  - 瀵?WindowsApps stub 缁欏嚭鏄庣‘璀﹀憡
  - 缁熶竴鎺ㄨ崘鍚姩鍣?/ wrapper 琛屼负
  - 鏂囨。鍚屾鏄庣‘ Windows 鎺ㄨ崘杩愯娉?- 瀹炴柦鑼冨洿锛?  - `claude_code/main.py`
  - `README.md`
  - 鍙€夋柊澧?`scripts/` 涓嬭緟鍔╁惎鍔ㄨ剼鏈?- 瀹屾垚绋嬪害锛?  - doctor 杈撳嚭鑳借瘖鏂В閲婂櫒椋庨櫓
  - Windows 鐢ㄦ埛涓嶄細璇互涓?stub 鍙敤
  - 椤圭洰鍏ュ彛鏂囨。娓呮鏍囨敞鎺ㄨ崘瑙ｉ噴鍣?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氳В閲婂櫒璺緞璇嗗埆閫昏緫
  - `T2`锛歞octor 杈撳嚭鍒嗘敮
  - `T4`锛歐indowsApps stub 鍥炲綊鐢ㄤ緥
- 寤鸿娴嬭瘯鏂囦欢锛?  - 鏂板 `tests/test_doctor_runtime.py`
- 鎵嬪伐楠屾敹锛?  - 妯℃嫙 / 妫€鏌?doctor 杈撳嚭
- 闈炵洰鏍囷細
  - 涓嶅仛瀹屾暣瀹夎鍣?- 鍓嶇疆渚濊禆锛歚P0-01`

## P0-09 娴嬭瘯涓存椂浜х墿娓呯悊涓庨殧绂?
- 鍗″彿锛歚P0-09`
- 浼樺厛绾э細`P1`
- 瑙ｅ喅闂锛?  - `tests/.tmp_plugins/` 瀛樺湪娈嬬暀鐩綍
  - 娴嬭瘯闅旂鎬т笌浠撳簱鏁存磥鎬т笉瓒?- 鐮斿彂鍔熻兘锛?  - 淇 plugin 娴嬭瘯鐨勬竻鐞嗛€昏緫
  - 澧炶ˉ `.gitignore` 鎴栨祴璇?teardown
  - 纭繚 pytest 缁撴潫鍚庝笉鏂板鑴忕洰褰?- 瀹炴柦鑼冨洿锛?  - `tests/test_plugins_runtime.py`
  - `.gitignore`
  - 瑙嗛渶瑕佽皟鏁?plugin fixture
- 瀹屾垚绋嬪害锛?  - 鏈湴瀹屾暣 pytest 鍚庝笉鍐嶆畫鐣欐柊澧?`.tmp_*` / `.tmp_plugins/*`
  - 娴嬭瘯浜掍笉姹℃煋
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T2`锛歠ixture cleanup 鏂█
  - `T4`锛氶噸澶嶈繍琛?pytest 涓嶇疮璁℃畫鐣?- 寤鸿娴嬭瘯鏂囦欢锛?  - 鎵╁睍 `tests/test_plugins_runtime.py`
- 鎵嬪伐楠屾敹锛?  - 杩炵画璺戜袱娆?pytest
  - 妫€鏌ュ伐浣滃尯鑴忔枃浠?- 闈炵洰鏍囷細
  - 涓嶆竻鐞嗙敤鎴风湡瀹炶繍琛屾暟鎹?- 鍓嶇疆渚濊禆锛氭棤

## P0-10 Phase 0 鍥炲綊闂ㄧ

- 鍗″彿锛歚P0-10`
- 浼樺厛绾э細`P0`
- 瑙ｅ喅闂锛?  - 鐜版湁娴嬭瘯鍒嗗竷杈冩暎锛屾病鏈夊洿缁?Phase 0 涓婚摼寤虹珛鏄庣‘闂ㄧ
- 鐮斿彂鍔熻兘锛?  - 瀹氫箟涓€缁勫繀椤婚€氳繃鐨?runtime regression tests
  - 澧炲姞鎸変富閾惧垎缁勭殑 pytest marker 鎴栬剼鏈叆鍙?  - 鏄庣‘鎻愪氦鍓嶅繀璺戝懡浠?- 瀹炴柦鑼冨洿锛?  - `pytest.ini`
  - `scripts/` 涓嬫牎楠岃剼鏈紙濡傞渶瑕侊級
  - 娴嬭瘯鏂囦欢鏍囪鏁寸悊
- 瀹屾垚绋嬪害锛?  - 鑳戒竴鏉″懡浠ゆ墽琛?P0 涓婚摼鍥炲綊
  - 鍥㈤槦鐭ラ亾鈥滃紑宸ュ墠/鍚堝苟鍓嶅繀椤昏窇浠€涔堚€?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - 鏈崱鏈川涓婃槸娴嬭瘯缁勭粐鍗?  - 闇€瑕佽ˉ 1 涓祴璇曞叆鍙ｈ剼鏈垨 marker 楠岃瘉
- 寤鸿娴嬭瘯鏂囦欢锛?  - 濡傞渶鏂板锛歚tests/test_phase0_regression_contract.py`
- 鎵嬪伐楠屾敹锛?  - 鎵ц涓€鏉?phase0 gate 鍛戒护骞堕獙璇侀€氳繃
- 闈炵洰鏍囷細
  - 涓嶈姹傛鏃舵帴 CI SaaS
- 鍓嶇疆渚濊禆锛?  - `P0-02` ~ `P0-09`

## 6. Phase 1 浠诲姟鍗″崟

## P1-01 daemon / API 鎺у埗闈?
- 鍗″彿锛歚P1-01`
- 浼樺厛绾э細`P1`
- 瑙ｅ喅闂锛?  - 褰撳墠 CLI 鏄帤瀹㈡埛绔紝IDE/desktop/web/CI 鏃犳硶鍏辩敤鎵ц鍚庣
- 鐮斿彂鍔熻兘锛?  - 鎻愪緵鏈湴 daemon/API 灞?  - 鎶界 session銆乼ask銆乼ool execution銆乤rtifact 璁块棶鎺ュ彛
  - CLI 鏀逛负 daemon client 鐨勪笂灞傚叆鍙?- 瀹炴柦鑼冨洿锛?  - 鏂板 `claude_code/server/` 鎴栫瓑浠锋帶鍒堕潰妯″潡
  - 璋冩暣 `main.py`
  - 澶嶇敤 `app.py`
- 瀹屾垚绋嬪害锛?  - 鍗曟満鍙惎鍔?daemon
  - CLI 涓?daemon 鍙叡浜竴濂楁墽琛屾牳蹇?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛欰PI schema / request validation
  - `T2`锛歴erver service 灞傝涓?  - `T3`锛歝lient -> server -> runtime 涓€鏉″畬鏁撮摼
  - `T4`锛歞aemon 鏈惎鍔?/ 瓒呮椂 / 浼氳瘽涓嶅瓨鍦?- 鍓嶇疆渚濊禆锛歚P0-01`銆乣P0-10`

## P1-02 event journal 浜嬩欢鏃ュ織

- 鍗″彿锛歚P1-02`
- 浼樺厛绾э細`P1`
- 瑙ｅ喅闂锛?  - prompt銆乼ool銆乼ask銆乸ermission 鍐崇瓥涓嶅彲鍥炴斁锛屼笉鍙璁?- 鐮斿彂鍔熻兘锛?  - 瀹氫箟缁熶竴浜嬩欢妯″瀷
  - 鍐欏叆 prompt/message/tool/task/permission/artifact 浜嬩欢
  - 鎻愪緵鏌ヨ涓?replay 鍩虹鑳藉姏
- 瀹炴柦鑼冨洿锛?  - 鏂板 `claude_code/services/event_journal.py` 鎴栫瓑浠锋ā鍧?  - 鎺ュ叆 `QueryEngine`銆乣TaskManager`
- 瀹屾垚绋嬪害锛?  - 鎵€鏈夊叧閿富閾惧姩浣滃彲浜х敓缁撴瀯鍖栦簨浠?  - 鏀寔鎸?session 鏌ヨ浜嬩欢娴?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氫簨浠?schema銆佸簭鍒楀寲銆乿ersioning
  - `T2`锛歸riter/reader correctness
  - `T3`锛歲uery -> tool -> task 浜嬩欢閾?  - `T4`锛氶儴鍒嗗啓鍏ュけ璐ャ€佷贡搴忔仮澶?- 鍓嶇疆渚濊禆锛歚P1-01`

## P1-03 SQLite runtime state backend

- 鍗″彿锛歚P1-03`
- 浼樺厛绾э細`P1`
- 瑙ｅ喅闂锛?  - file/memory backend 瀵规仮澶嶃€佹绱€佸瀹炰緥鍓嶅噯澶囦笉瓒?- 鐮斿彂鍔熻兘锛?  - 涓?session/task/event 鎻愪緵 SQLite backend
  - 淇濈暀 file backend 浣滀负鍏煎灞傛垨 fallback
  - 鏄庣‘ migration 涓?schema version
- 瀹炴柦鑼冨洿锛?  - `claude_code/tasks/factory.py`
  - `claude_code/tasks/repository.py`
  - session/event 鐩稿叧瀛樺偍妯″潡
- 瀹屾垚绋嬪害锛?  - 鑷冲皯鍙敤 SQLite 鎸佷箙鍖?task/session/event
  - 鍗曟満閲嶅惎鍚庡彲鎭㈠鏍稿績杩愯鎬?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歴chema init / migration
  - `T2`锛歳epository CRUD contract
  - `T3`锛氶噸鍚仮澶?  - `T4`锛氭暟鎹簱鎹熷潖銆侀攣鍐茬獊銆侀噸澶嶅垵濮嬪寲
- 鍓嶇疆渚濊禆锛歚P1-02`

## P1-04 active memory 鎺ュ叆杩愯鏃?
- 鍗″彿锛歚P1-04`
- 浼樺厛绾э細`P1`
- 瑙ｅ喅闂锛?  - `SessionMemory` 鐜板湪鏄绔?KV锛屼笉褰卞搷涓诲璇濅笂涓嬫枃
- 鐮斿彂鍔熻兘锛?  - 璁?memory 涓?context builder/runtime 鑱斿姩
  - 瀹氫箟 memory scope锛歶ser/project/local
  - 鏀寔鏄惧紡鍐欏叆銆佹寜闇€娉ㄥ叆銆佸懡涓粺璁?- 瀹炴柦鑼冨洿锛?  - `claude_code/services/memory_service.py`
  - `claude_code/context/builder.py`
  - `claude_code/agents/builtin.py`
- 瀹屾垚绋嬪害锛?  - memory 鎴愪负杩愯鏃剁湡瀹炶緭鍏ワ紝鑰岄潪鏃佽矾瀛樺偍
  - agent / main query 鍙€夋嫨涓嶅悓 memory scope
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歯amespace / key / search 琛屼负
  - `T2`锛歝ontext builder memory 娉ㄥ叆
  - `T3`锛歲uery 鎵ц鏃跺懡涓?memory
  - `T4`锛氱┖ memory / 鎹熷潖 memory / scope 闅旂
- 鍓嶇疆渚濊禆锛歚P0-06`銆乣P1-02`

## P1-05 hooks / permission / audit 鏀舵暃

- 鍗″彿锛歚P1-05`
- 浼樺厛绾э細`P1`
- 瑙ｅ喅闂锛?  - hooks銆乸ermissions銆乪vent journal 浠嶆槸鍒嗙珛鑳藉姏
- 鐮斿彂鍔熻兘锛?  - 缁熶竴 hook 浜嬩欢銆乸ermission decision銆乤udit event
  - 褰㈡垚涓€娆℃墽琛岀殑瀹屾暣瀹¤閾?  - 涓烘湭鏉?org policy 閾哄簳
- 瀹炴柦鑼冨洿锛?  - `claude_code/permissions.py`
  - `claude_code/services/hooks_manager.py`
  - event journal 鐩稿叧妯″潡
- 瀹屾垚绋嬪害锛?  - 姣忔 tool call 鑷冲皯鍏峰 request -> decision -> hook -> result 鐨勯棴鐜褰?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T2`锛歱ermission + hook + event 鑱斿姩
  - `T3`锛氱湡瀹?tool 鎵ц瀹¤閾?  - `T4`锛歞eny / timeout / partial failure
- 鍓嶇疆渚濊禆锛歚P0-07`銆乣P1-02`

## P1-06 CLI thin client 杩佺Щ

- 鍗″彿锛歚P1-06`
- 浼樺厛绾э細`P1`
- 瑙ｅ喅闂锛?  - CLI 涓庢帶鍒堕潰鑰﹀悎杩囨繁锛屼笉鍒╀簬 IDE/CI 鍏辩敤
- 鐮斿彂鍔熻兘锛?  - CLI 鍙戣姹傜粰鏈湴 runtime server/daemon
  - 淇濈暀鍗曡繘绋?fallback 妯″紡
  - 缁熶竴杈撳嚭涓庨敊璇涔?- 瀹炴柦鑼冨洿锛?  - `claude_code/main.py`
  - CLI/REPL client adapter
- 瀹屾垚绋嬪害锛?  - CLI 浣滀负 runtime 鍓嶇瀛樺湪锛岃€岄潪鎵ц鍐呮牳鏈韩
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T2`锛歝lient adapter 琛屼负
  - `T3`锛欳LI -> daemon 瀹屾暣涓婚摼
  - `T4`锛歞aemon 涓嶅彲鐢?fallback
- 鍓嶇疆渚濊禆锛歚P1-01`

## 7. Phase 2 浠诲姟鍗″崟

## P2-01 澶?Agent supervisor

- 鍗″彿锛歚P2-01`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - 褰撳墠 agent 鏇村儚鈥滃崟娆″瓙浠诲姟鎵ц鍣ㄢ€濓紝涓嶆槸鎺у埗闈?- 鐮斿彂鍔熻兘锛?  - agent DAG
  - budget / timeout / retry / ownership
  - parent-child artifact passing
- 瀹屾垚绋嬪害锛?  - 鑷冲皯鏀寔骞惰 agent + 姹囨€绘敹鍙?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歡raph / budget / timeout 鐘舵€佹満
  - `T2`锛歴upervisor 璋冨害
  - `T3`锛氬苟琛?agent 鎵ц
  - `T4`锛氬瓙 agent 澶辫触鎭㈠
- 鍓嶇疆渚濊禆锛歚P1-01`銆乣P1-02`

## P2-02 artifact bus 涓庡啿绐佹敹鏁?
- 鍗″彿锛歚P2-02`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - 澶?agent 杈撳嚭缂哄皯缁撴瀯鍖?artifact 浜ゆ崲灞?- 鐮斿彂鍔熻兘锛?  - 缁熶竴 artifact schema
  - patch / note / diff / report / finding 娴佽浆
  - 鍐茬獊妫€娴嬩笌鍚堝苟绛栫暐
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歛rtifact schema
  - `T2`锛歱roducer/consumer
  - `T3`锛氬 agent artifact 姹囨祦
  - `T4`锛氬啿绐佸悎骞跺け璐?- 鍓嶇疆渚濊禆锛歚P2-01`

## P2-03 IDE 闆嗘垚锛圴S Code first锛?
- 鍗″彿锛歚P2-03`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - 褰撳墠浠撳簱缂哄皯鐪熸鍙敤鐨?IDE workflow
- 鐮斿彂鍔熻兘锛?  - VS Code client
  - daemon 杩炴帴
  - diff銆乼ask銆乻ession銆乫indings 灞曠ず
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T2`锛歝lient protocol adapter
  - `T3`锛欼DE -> daemon 鏍稿績閾?  - `T5`锛氫汉宸ヤ氦浜掗獙鏀朵负涓?- 鍓嶇疆渚濊禆锛歚P1-06`

## P2-04 GitHub / CI 宸ヤ綔娴?agent

- 鍗″彿锛歚P2-04`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - 褰撳墠鑳藉姏涓昏鍋滅暀鍦ㄦ湰鍦?CLI锛屾棤娉曡繘鍏ュ洟闃熷崗浣滈棴鐜?- 鐮斿彂鍔熻兘锛?  - issue -> plan -> code -> test -> review -> PR 宸ヤ綔娴?  - CI 鐜鐨?headless execution 妯″紡
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T2`锛歸orkflow state machine
  - `T3`锛歠ake repo / fake PR 涓婚摼
  - `T4`锛氭潈闄愪笉瓒?/ repo 鐘舵€佷笉骞插噣 / 缃戠粶澶辫触
- 鍓嶇疆渚濊禆锛歚P1-01`銆乣P1-02`

## P2-05 缁勭粐绾х瓥鐣ヤ笌瀹¤闈㈡澘

- 鍗″彿锛歚P2-05`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - 鍥㈤槦鍦烘櫙涓嬬己涔忔不鐞嗐€佸鎵广€佸璁°€佸畨鍏ㄨ竟鐣?- 鐮斿彂鍔熻兘锛?  - policy model
  - approval queue
  - secret redaction
  - audit query / reporting
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歱olicy matcher / redaction rules
  - `T2`锛歛pproval state transitions
  - `T3`锛氭墽琛屽璁￠摼闂幆
  - `T4`锛氱瓥鐣ュ啿绐?/ 鏈鎵规墽琛岄樆鏂?- 鍓嶇疆渚濊禆锛歚P1-05`

## P2-06 Linux 缁熶竴楠屽案闂ㄧ

- 鍗″彿锛歚P2-06`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - 褰撳墠姣忓紶鍗″悇鏈?gate 鑴氭湰锛屼絾缂哄皯涓€娆℃€х粺涓€鎵ц娓呭崟锛屼笉鍒╀簬 Linux 闃舵鍏ㄩ噺楠屽案
- 鐮斿彂鍔熻兘锛?  - 鑱氬悎 `P0-01` 鍒?`P2-05` 鍏ㄩ摼璺叧閿祴璇曡剼鏈竻鍗?  - 鎻愪緵 Linux 缁熶竴鎵ц鍏ュ彛鑴氭湰
  - 寤虹珛 unified gate manifest 鐨?contract test锛岄伩鍏嶆竻鍗曟紓绉?- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歮anifest 瀛樺湪鎬т笌鏂囦欢鏄犲皠鏍￠獙
  - `T2`锛氬懡浠ょ敓鎴愰『搴忎笌鏍煎紡濂戠害
  - `T3`锛歀inux 闃舵鎸夋竻鍗曢€愭潯鎵ц锛堟湰鍦颁笉鎵ц锛?  - `T4`锛氭柊澧?鍒犲噺娴嬭瘯鏂囦欢鏃跺绾﹀洖褰掓彁绀?- 鍓嶇疆渚濊禆锛歚P2-05`

## P2-07 Agent 杩愯鏃朵竴鑷存€э紙sync/background parity锛?
- 鍗″彿锛歚P2-07`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `AgentTool` 鐨勫悓姝ヤ笌鍚庡彴璺緞鍦?runtime context 缁ф壙涓婂瓨鍦ㄦ紓绉婚闄?  - 鍚庡彴 agent 浠诲姟缂哄皯 session/conversation 绛夊璁″厓鏁版嵁锛屼笉鍒╀簬鍥炴斁涓庢不鐞?- 鐮斿彂鍔熻兘锛?  - 瀵归綈 sync/background 瀛?agent 鍦?`working_directory`銆乣tool_registry`銆乣permission_mode`銆乣provider/model`銆乣memory_scope` 鐨勮涓?  - 灏?`session_id`銆乣conversation_id`銆乺untime context 瀛楁鍐欏叆鍚庡彴浠诲姟 metadata
  - 璁╁悗鍙拌矾寰勪紭鍏堝鐢ㄤ笂灞?runtime `TaskManager`锛岄伩鍏嶅叏灞€鍗曚緥婕傜Щ
- 瀹炴柦鑼冨洿锛?  - `claude_code/tools/base.py`
  - `claude_code/engine/query.py`
  - `claude_code/tools/agent/__init__.py`
  - `claude_code/tasks/manager.py`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T2`锛歴ync/background context 缁ф壙涓€鑷存€?  - `T3`锛氬悗鍙颁换鍔?metadata 瀹¤瀛楁瀹屾暣鎬?  - `T4`锛歱rovider/model 缁ф壙鍥炲綊锛堟湰鍦?provider 涓?Claude model alias 宸紓锛?- 鍓嶇疆渚濊禆锛歚P2-01`銆乣P2-06`

## P2-08 鑷畾涔?Agent 鐩綍鍔犺浇闂幆锛?claude/agents锛?
- 鍗″彿锛歚P2-08`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - Python 鐗堟湰 `AgentTool` 鍙敮鎸佸唴缃?`BUILTIN_AGENTS`锛屾湭褰㈡垚 `.claude/agents/*.md` 鐨勫姞杞介棴鐜?  - `subagent_type` 鎵句笉鍒版椂鍙娴嬫€т笉瓒筹紝鏃犳硶鍚屾椂鐪嬪埌 custom + builtin 鍙敤绫诲瀷
- 鐮斿彂鍔熻兘锛?  - 鏂板 `.claude/agents/*.md` loader锛屾敮鎸?YAML frontmatter + prompt body 瑙ｆ瀽
  - 鏀寔浠庡綋鍓嶇洰褰曞悜涓婃悳绱㈠埌 git 鏍圭殑澶氱骇 `.claude/agents`锛屽苟鎸夆€滆繎璺緞瑕嗙洊杩滆矾寰勨€濆悎骞?  - 鍦?`AgentTool` 涓帴鍏?custom agent lazy-load锛屼紭鍏堢骇 `custom > builtin`
  - `Unknown agent type` 閿欒鎻愮ず杈撳嚭鑱斿悎鍙敤 agent 鍒楄〃
- 瀹炴柦鑼冨洿锛?  - `claude_code/agents/loader.py`
  - `claude_code/tools/agent/__init__.py`
  - `scripts/run_p2_custom_agents_loader_gate.py`
  - `scripts/run_linux_unified_gate.py`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歠rontmatter 瑙ｆ瀽涓庡瓧娈靛綊涓€鍖栵紙tools/disallowedTools/memory/maxTurns锛?  - `T2`锛氬绾х洰褰曡鐩栫瓥鐣ワ紙root -> nested锛?  - `T3`锛欰gentTool custom 瑕嗙洊 builtin 瑙ｆ瀽閾?  - `T4`锛歩nvalid YAML / 缂哄瓧娈靛閿?+ unknown type 鑱斿悎鍙敤娓呭崟
- 鍓嶇疆渚濊禆锛歚P2-07`

## P2-09 Linux 缁熶竴楠屽案鎵ц闂ㄧ
- 鍗″彿锛歚P2-09`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-06` 褰撳墠鍙緭鍑哄懡浠ゆ竻鍗曪紝涓嶇洿鎺ユ彁渚?Linux 闃舵鐨勪竴閿墽琛屻€佹姤鍛婃矇娣€涓庡け璐ョ瓥鐣ユ帶鍒躲€?  - 缁熶竴楠屽案閾剧己灏戞爣鍑嗗寲浜х墿锛坖unit xml + summary json锛夛紝涓嶅埄浜?CI 姹囨€讳笌鍥炴斁銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 Linux 鎵ц闂ㄧ鑴氭湰锛屽鐢?`run_linux_unified_gate.py` manifest銆?  - 鎻愪緵 `--dry-run` / `--print-commands` / `--continue-on-failure` / `--report-dir` 鑳藉姏銆?  - 椤哄簭鎵ц姣忔潯 pytest 鍛戒护骞朵骇鍑烘瘡鏉＄敤渚嬬殑 `--junitxml`锛屾渶缁堝啓鍏ョ粺涓€ `summary.json`銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_unified_execution_gate.py`
  - `scripts/run_linux_unified_gate.py`
  - `tests/test_p2_linux_unified_execution_gate_runtime.py`
  - `README.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氭墽琛岄棬绂佸懡浠ょ敓鎴愪弗鏍艰窡闅?unified manifest 椤哄簭銆?  - `T2`锛氶澶?pytest 鍙傛暟閫忎紶濂戠害涓?junit 璺緞濂戠害銆?  - `T3`锛歀inux 闃舵鎵ц鍏ュ彛鍙?dry-run锛屼笉鍦ㄦ湰鍦拌繍琛屾祴璇曘€?  - `T4`锛歮anifest 鍙樻洿鍚庢墽琛岄棬绂佸绾︽祴璇曞彲鍙婃椂鎷︽埅婕傜Щ銆?- 鍓嶇疆渚濊禆锛歚P2-06`銆乣P2-08`

## P2-10 JetBrains IDE 闆嗘垚锛圛ntelliJ / PyCharm锛?- 鍗″彿锛歚P2-10`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-03` 浠呰鐩?`VS Code first` 閫傞厤锛孞etBrains 鐢熸€佺己灏戞爣鍑嗗寲蹇収閫傞厤灞傘€?  - 鐜版湁 IDE payload 铏藉彲澶嶇敤锛屼絾缂哄皯 JetBrains 渚у彲鐩存帴娑堣垂鐨?inspection 缁撴瀯鏄犲皠銆?- 鐮斿彂鍔熻兘锛?  - 鍦?`ide_adapter` 澧炲姞 `JetBrainsClientAdapter`銆?  - 灏?daemon `workspace.findings` 鏄犲皠涓?JetBrains inspection 缁撴瀯锛坰everity -> highlight锛夈€?  - 淇濇寔 daemon API 涓嶅彉锛岄€傞厤灞傚畬鎴愨€滃悓 payload锛屽 IDE 璇箟鈥濇敹鏁涖€?- 瀹炴柦鑼冨洿锛?  - `claude_code/server/ide_adapter.py`
  - `claude_code/server/__init__.py`
  - `tests/test_p2_jetbrains_ide_integration_runtime.py`
  - `scripts/run_p2_jetbrains_ide_integration_gate.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛欽etBrains adapter 鍗忚褰掍竴鍖栵紙project_root/vcs/sessions/tasks锛夈€?  - `T2`锛歠indings -> inspections 瀛楁鏄犲皠涓?severity/highlight 濂戠害銆?  - `T3`锛氫繚鎸?daemon `ide/workspace` payload 鍏煎锛屼笉鏂板璺敱銆?  - `T4`锛氶潪娉?line/severity 杈撳叆瀹归敊銆?- 鍓嶇疆渚濊禆锛歚P2-03`銆乣P2-09`

## P2-11 Linux 鍒嗙墖骞惰楠屽案闂ㄧ
- 鍗″彿锛歚P2-11`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-09` 浠呮敮鎸佸崟杩涚▼椤哄簭鎵ц锛孡inux 闃舵鏃犳硶鐩存帴鎸?CI job 鍒嗙墖骞惰锛屾暣浣撳洖褰掕€楁椂楂樸€?  - 缂哄皯鍒嗙墖绾?summary 鍏冩暟鎹紝涓嶅埄浜庡 job 鍥炴敹闃舵鍋氱粺涓€鑱氬悎銆?- 鐮斿彂鍔熻兘锛?  - 鍦?`run_p2_linux_unified_execution_gate.py` 澧炲姞 `--shard-total` / `--shard-index`銆?  - 鎸?unified manifest 椤哄簭鍋氱‘瀹氭€у垎鐗囬€夋嫨锛堝悓涓€杈撳叆濮嬬粓绋冲畾鍒囩墖锛夈€?  - summary 澧炲姞 `shard_total` / `shard_index` / `manifest_total_tests` 瀛楁銆?  - 淇濇寔 `--dry-run` / `--print-commands` 璺緞鍙褰撳墠鍒嗙墖瑕嗙洊鑼冨洿銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_unified_execution_gate.py`
  - `tests/test_p2_linux_unified_execution_gate_runtime.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氬垎鐗囬€夋嫨涓?manifest 椤哄簭濂戠害锛坉eterministic slicing锛夈€?  - `T2`锛氶潪娉曞垎鐗囧弬鏁版嫆缁濆绾︼紙`shard_total < 1` / `shard_index` 瓒婄晫锛夈€?  - `T3`锛歴ummary 鍒嗙墖鍏冩暟鎹绾︺€?  - `T4`锛氶澶?pytest 鍙傛暟閫忎紶銆乯unit 璺緞濂戠害缁х画淇濇寔銆?- 鍓嶇疆渚濊禆锛歚P2-09`

## P2-12 Linux 鍒嗙墖楠屽案姹囨€婚棬绂?- 鍗″彿锛歚P2-12`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-11` 宸叉敮鎸佸垎鐗囧苟琛屾墽琛岋紝浣嗙己灏?Linux 鍥炴敹闃舵鐨勭粺涓€姹囨€诲叆鍙ｏ紝鏃犳硶缁欏嚭鍏ㄥ眬閫氳繃/澶辫触鍒ゅ畾銆?  - 澶氫釜 shard 鐨?`summary.json` 缂哄皯涓€鑷存€ф牎楠岋紙缂虹墖/閲嶅鐗?manifest 婕傜Щ锛夛紝瀹规槗璁?CI 璇垽銆?- 鐮斿彂鍔熻兘锛?  - 鏂板鍒嗙墖姹囨€婚棬绂佽剼鏈紝鏀寔 `--summary` / `--summary-glob` / `--artifacts-dir` 鑷姩鍙戠幇 summary 鏂囦欢銆?  - 鍚堝苟 shard 缁撴灉骞惰緭鍑?`merged_summary.json`锛屾矇娣€ `overall_status`銆乣structural_issues`銆乣shards_missing` 涓庡叏灞€ totals銆?  - 瀵瑰叧閿粨鏋勫仛濂戠害鏍￠獙锛氬瓧娈靛畬鏁存€с€乣shard_index` 鑼冨洿銆乣passed+failed<=total_tests`銆乵anifest/鍒嗙墖鎬绘暟涓€鑷存€с€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_shard_aggregation_gate.py`
  - `tests/test_p2_linux_shard_aggregation_gate_runtime.py`
  - `tests/test_p2_linux_unified_execution_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歴ummary 鍙戠幇绛栫暐鍘婚噸濂戠害锛坉irect + glob + artifacts-dir锛夈€?  - `T2`锛歴ummary 鍩虹瀛楁鏍￠獙涓庣被鍨嬬害鏉熷绾︺€?  - `T3`锛氬叏鍒嗙墖瑕嗙洊鏃剁殑鑱氬悎 totals 涓?passed 鐘舵€佸绾︺€?  - `T4`锛氱己鐗?鎬绘暟婕傜Щ鏃剁殑 structural issue 涓?failed 鐘舵€佸绾︺€?- 鍓嶇疆渚濊禆锛歚P2-11`

## P2-13 Linux 鏈€缁堟姤鍛婂彂甯冮棬绂?- 鍗″彿锛歚P2-13`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-12` 浠呰緭鍑?`merged_summary.json`锛岀己灏?Linux 鍥炴敹闃舵鍙洿鎺ュ綊妗ｄ笌灞曠ず鐨勬渶缁堟姤鍛婁骇鐗┿€?  - 瀵?`overall_status` 缂哄皯鈥滃啀璁＄畻鏍￠獙鈥濅笌鍙戝竷濂戠害锛孋I 渚ч毦浠ョǔ瀹氭秷璐规渶缁堢粨璁恒€?- 鐮斿彂鍔熻兘锛?  - 鏂板鏈€缁堟姤鍛婂彂甯冮棬绂佽剼鏈紝璇诲彇 `merged_summary.json` 骞跺仛瀛楁濂戠害鏍￠獙銆?  - 杈撳嚭 `final_report.json` 涓?`final_report.md`锛堢姸鎬併€佸垎鐗囥€乼otals銆乻tructural issues銆乶otes锛夈€?  - 瀵?`overall_status` 鎵ц computed-vs-reported 涓€鑷存€у鏍革紝涓嶄竴鑷存椂寮哄埗澶辫触銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_report_publish_gate.py`
  - `tests/test_p2_linux_report_publish_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歮erged summary 蹇呭～瀛楁涓庣被鍨嬪绾︽牎楠屻€?  - `T2`锛歨appy path 涓嬫渶缁堢姸鎬佷笌 totals 鍙戝竷濂戠害銆?  - `T3`锛歳eported status 涓?computed status 涓嶄竴鑷存椂澶辫触濂戠害銆?  - `T4`锛歁arkdown 鎶ュ憡缁撴瀯濂戠害锛圱otals/Shards/Structural Issues/Notes锛夈€?- 鍓嶇疆渚濊禆锛歚P2-12`

## P2-14 Linux 缁熶竴楠屽案鍏ㄩ摼缂栨帓闂ㄧ
- 鍗″彿锛歚P2-14`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-09` / `P2-12` / `P2-13` 宸叉媶鍒嗕负澶氶樁娈佃剼鏈紝浣嗙己灏戜竴鏉?Linux 涓€閿覆鑱旀墽琛屽叆鍙ｃ€?  - 澶氶樁娈垫墜宸ユ嫾瑁呭懡浠ゆ槗婕傜Щ锛屽け璐ョ瓥鐣ヤ笌鍙傛暟閫忎紶鍦?CI 渚ч毦缁熶竴銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 pipeline gate锛屾寜 `execution -> aggregation -> publish` 缂栨帓鎵ц銆?  - 鏀寔 `--skip-execution` / `--skip-aggregation` / `--skip-publish`锛岃鐩栧崟鏈轰笌澶?job 鍥炴敹鍦烘櫙銆?  - 鏀寔 `--print-commands` / `--dry-run` 浜у嚭鍙璁″懡浠ゆ竻鍗曪紝鏀寔 `--fail-fast` 澶辫触鎺у埗銆?  - 鏀寔 execution 闃舵 pytest 棰濆鍙傛暟閫忎紶锛坄--` 杞彂鍒?`P2-09`锛夈€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_unified_pipeline_gate.py`
  - `tests/test_p2_linux_unified_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氶粯璁や笁闃舵鍛戒护鐢熸垚濂戠害锛坋xecution summary 鑷姩娉ㄥ叆 aggregation锛夈€?  - `T2`锛歚skip-execution` 涓嬪閮?summary/glob/artifacts 鍙傛暟閫忎紶濂戠害銆?  - `T3`锛氬叏璺宠繃妯″紡杩斿洖绌?pipeline 濂戠害銆?  - `T4`锛歱ytest 棰濆鍙傛暟閫忎紶濂戠害銆?- 鍓嶇疆渚濊禆锛歚P2-13`

## P2-15 Linux 鍒嗙墖鎵ц璁″垝鐢熸垚闂ㄧ
- 鍗″彿锛歚P2-15`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-11`/`P2-14` 宸叉敮鎸佸垎鐗囨墽琛屼笌鍏ㄩ摼缂栨帓锛屼絾 Linux CI fan-out job 浠嶉渶鎵嬪伐鎷兼帴 `shard_index` 鍛戒护锛屽鏄撴紓绉汇€?  - 缂哄皯鈥滄墽琛屽墠鈥濊鍒掍骇鐗╋紝CI 鍥炴敹闃舵闅句互瀵圭収鏍￠獙鍒嗙墖瑕嗙洊鏄惁瀹屾暣銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 shard plan gate锛屽熀浜?unified manifest 鐢熸垚纭畾鎬?`shard_plan.json`銆?  - 姣忎釜鍒嗙墖杈撳嚭锛歚test_files`銆乣report_dir`銆乣summary_path`銆乣execution command`銆乣command_parts`銆?  - 鏀寔 `--print-commands`/`--dry-run` 鐢ㄤ簬 CI 缂栨帓鎺㈡祴锛涙敮鎸?pytest 棰濆鍙傛暟閫忎紶锛坄--`锛夈€?  - 瀵?`shard_total` 涓?manifest 鏂囦欢瀛樺湪鎬у仛鍓嶇疆濂戠害鏍￠獙锛岄潪娉曡緭鍏ョ洿鎺ュけ璐ャ€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_shard_plan_gate.py`
  - `tests/test_p2_linux_shard_plan_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氬垎鐗囧垏鐗囩‘瀹氭€у绾︼紙涓?`P2-11` slicing 涓€鑷达級銆?  - `T2`锛氬垎鐗囨墽琛屽懡浠や笌 pytest 鍙傛暟閫忎紶濂戠害銆?  - `T3`锛氶潪娉?`shard_total` 鎷掔粷濂戠害銆?  - `T4`锛氳緭鍑?`summary_path/report_dir` 瀛楁濂戠害銆?- 鍓嶇疆渚濊禆锛歚P2-14`

## P2-16 Linux CI Matrix 瀵煎嚭闂ㄧ
- 鍗″彿锛歚P2-16`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-15` 宸蹭骇鍑?`shard_plan.json`锛屼絾 Linux CI 浠嶉渶鎵嬪伐鎶婂垎鐗囪鍒掕浆涓?matrix 鍙橀噺锛屾槗浜х敓缂栨帓婕傜Щ銆?  - fan-out 涓?fan-in 涔嬮棿缂哄皯缁熶竴鐨?`summary_paths` 鍥炴敹娓呭崟锛屽鑷村洖鏀堕樁娈靛弬鏁版嫾瑁呬笉绋冲畾銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 CI matrix gate锛屼粠 `shard_plan.json` 鐢熸垚鍙洿鎺ユ秷璐圭殑 `ci_matrix.json`銆?  - 杈撳嚭鏍囧噯 `matrix.include` 鏉＄洰锛坄shard_index/shard_total/command/command_parts/report_dir/summary_path`锛夈€?  - 杈撳嚭 `summary_paths` 鍥炴敹娓呭崟锛屼緵 `P2-12` 鑱氬悎闃舵鐩存帴浣跨敤銆?  - 鏀寔 `--github-output` 鍐欏叆 GitHub Actions output 鏂囦欢锛涙敮鎸?`--skip-empty-shards` 杩囨护绌哄垎鐗囥€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_matrix_gate.py`
  - `tests/test_p2_linux_ci_matrix_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歮atrix include 椤哄簭涓庡瓧娈靛绾︺€?  - `T2`锛歚skip-empty-shards` 杩囨护濂戠害銆?  - `T3`锛欸itHub output 瀛楁鐢熸垚濂戠害锛坢atrix/summary_paths/selected_shards锛夈€?  - `T4`锛歚manifest_total_tests` 涓庡垎鐗?totals 涓嶄竴鑷存椂鎷掔粷濂戠害銆?- 鍓嶇疆渚濊禆锛歚P2-15`

## P2-17 Linux CI Workflow 璁″垝闂ㄧ
- 鍗″彿锛歚P2-17`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-16` 宸蹭骇鍑?`ci_matrix.json`锛屼絾 fan-out/fan-in CI job 浠嶉渶浜哄伐鎷兼帴鍥炴敹鍛戒护锛屽彂甯冮摼瀛樺湪鎵嬪伐婕傜Щ椋庨櫓銆?  - 缂哄皯缁熶竴 workflow 璁″垝浜х墿锛孋I 缂栨帓渚ф棤娉曠洿鎺ユ秷璐光€滃垎鐗囨墽琛?+ 姹囨€?+ 鍙戝竷鈥濆叏閾惧懡浠ゃ€?- 鐮斿彂鍔熻兘锛?  - 鏂板 CI workflow plan gate锛屼粠 `ci_matrix.json` 鐢熸垚 `ci_workflow_plan.json`銆?  - 杈撳嚭 `fan_out_jobs` 涓?`fan_out_matrix.include`锛堝惈 shard job command/command_parts/report/summary 淇℃伅锛夈€?  - 杈撳嚭 `fan_in` 姹囨€讳笌鍙戝竷鍛戒护锛坅ggregation/publish command + command_parts锛夛紝鐩存帴瀵规帴 `P2-12`/`P2-13`銆?  - 鏀寔 `--github-output` 鍐欏叆 GitHub Actions outputs锛坄fan_out_matrix`銆乣fan_in_summary_paths`銆乣aggregation_command`銆乣publish_command` 绛夛級銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_plan_gate.py`
  - `tests/test_p2_linux_ci_workflow_plan_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歸orkflow payload 涓?fan-out/fan-in 瀛楁涓庡懡浠ゅ绾︺€?  - `T2`锛欸itHub output 瀛楁鐢熸垚濂戠害銆?  - `T3`锛歚summary_paths` 涓?`matrix.include` 椤哄簭涓嶄竴鑷存椂鎷掔粷濂戠害銆?  - `T4`锛歚selected_shards` 涓?include 鏁伴噺涓嶄竴鑷存椂鎷掔粷濂戠害銆?- 鍓嶇疆渚濊禆锛歚P2-16`

## P2-18 Linux CI Workflow YAML 娓叉煋闂ㄧ
- 鍗″彿锛歚P2-18`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-17` 宸蹭骇鍑?`ci_workflow_plan.json`锛屼絾 CI 骞冲彴浠嶉渶浜哄伐缂栧啓/缁存姢 workflow YAML锛宖an-out/fan-in 鍛戒护鏄撴紓绉汇€?  - 缂哄皯鈥滆鍒掍骇鐗?-> 鍙墽琛?workflow 鏂囦欢鈥濈殑鏈€鍚庝竴璺筹紝瀵艰嚧闂ㄧ閾句粛瀛樺湪鎵嬪伐浠嬪叆鐐广€?- 鐮斿彂鍔熻兘锛?  - 鏂板 CI workflow YAML gate锛屼粠 `ci_workflow_plan.json` 娓叉煋 `.github/workflows/linux_unified_gate.yml`銆?  - 娓叉煋 fan-out matrix job锛堝垎鐗囨墽琛?+ summary artifact 涓婁紶锛変笌 fan-in job锛坅rtifact 鍥炴敹 + 鑱氬悎 + 鍙戝竷 + 鏈€缁堟姤鍛婁笂浼狅級銆?  - 杈撳嚭娓叉煋鍏冩暟鎹?`ci_workflow_render.json`锛岃褰?source plan銆乫an-in 鍛戒护銆佹姤鍛婅矾寰勪笌鍒嗙墖缁熻锛屼緵瀹¤杩借釜銆?  - 鏀寔 `--dry-run`/`--print-yaml` 蹇€熼獙鐪嬫覆鏌撶粨鏋滐紝涓嶅湪鏈湴瑙﹀彂娴嬭瘯鎵ц銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_yaml_gate.py`
  - `tests/test_p2_linux_ci_workflow_yaml_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歸orkflow YAML fan-out/fan-in 瀛楁涓庡懡浠ゆ覆鏌撳绾︺€?  - `T2`锛歳ender metadata 瀛楁濂戠害锛坰ource/workflow path/summary stats锛夈€?  - `T3`锛歚fan_in.summary_paths` 涓?`fan_out_matrix.include[*].summary_path` 椤哄簭涓嶄竴鑷存椂鎷掔粷濂戠害銆?  - `T4`锛歚selected_shards` 涓?include 鏁伴噺涓嶄竴鑷存椂鎷掔粷濂戠害銆?- 鍓嶇疆渚濊禆锛歚P2-17`

## P2-19 Linux CI Workflow 婕傜Щ鏍￠獙闂ㄧ
- 鍗″彿锛歚P2-19`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-18` 宸茶兘娓叉煋 workflow YAML 涓?metadata锛屼絾浠撳簱涓殑 `.github/workflows/linux_unified_gate.yml` 涓?`ci_workflow_render.json` 鍙兘琚墜宸ユ敼鍔ㄥ悗涓?`ci_workflow_plan.json` 鑴辫妭銆?  - 缂哄皯鈥滆鍒掍骇鐗?-> 娓叉煋浜х墿涓€鑷存€ф牎楠屸€濋棬绂侊紝CI 鍙兘鍦ㄦ紓绉荤姸鎬佷笅杩愯锛屽鑷?fan-out/fan-in 鍛戒护涓庢姤鍛婅矾寰勫け鐪熴€?- 鐮斿彂鍔熻兘锛?  - 鏂板 workflow sync gate锛屽熀浜?`ci_workflow_plan.json` 澶嶇畻鏈熸湜 workflow YAML 涓?metadata锛屽苟涓庡綋鍓嶄骇鐗╁仛涓€鑷存€ф瘮瀵广€?  - 杈撳嚭 drift 鎽樿锛坵orkflow_drift/metadata_drift/drift_count锛夛紝鏀寔 `--print-diff` 鎵撳嵃 unified diff 渚夸簬瀹¤銆?  - 鏀寔 `--write` 鍦ㄦ湰鍦版垨 CI 閲岃嚜鍔ㄥ洖鍐欐爣鍑嗕骇鐗╋紝鏀舵暃浜哄伐婕傜Щ銆?  - 鏀寔 `--strict-generated-at` 寮€鍚?metadata `generated_at` 涓ユ牸姣斿锛涢粯璁ゅ拷鐣ヨ瀛楁浠呮牎楠岀粨鏋勪笌鏍稿績鍐呭銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_sync_gate.py`
  - `tests/test_p2_linux_ci_workflow_sync_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氬綋 workflow/metadata 缂哄け鏃跺繀椤昏Е鍙?drift 鍒ゅ畾銆?  - `T2`锛氬綋 workflow 鍐呭琚敼鍐欐椂锛屽繀椤昏緭鍑?drift 涓庡彲璇?diff 濂戠害銆?  - `T3`锛氶粯璁ゆā寮忓拷鐣?metadata `generated_at` 婕傜Щ锛岄伩鍏嶆椂闂存埑鍣０璇姤銆?  - `T4`锛氬紑鍚?strict 妯″紡鏃讹紝`generated_at` 婕傜Щ蹇呴』瑙﹀彂鎷掔粷濂戠害銆?- 鍓嶇疆渚濊禆锛歚P2-18`

## P2-20 Linux CI Workflow 鍛戒护鎶ゆ爮闂ㄧ
- 鍗″彿锛歚P2-20`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-19` 宸茶兘鏍￠獙 plan->yaml/metadata 婕傜Щ锛屼絾灏氭湭绾︽潫 `ci_workflow_plan.json` 鍐?`command` 涓?`command_parts` 鐨勪竴鑷存€э紝瀛樺湪鈥滃瓧绗︿覆琚敼銆乸arts 鏈敼鈥濆鑷?CI 瀹為檯鎵ц鍋忕Щ鐨勯闄┿€?  - fan-out 涓?fan-in 鍛戒护涓殑鍏抽敭璺緞锛坄report_dir`銆乣summary_paths`銆乣merged_summary/final_report`锛夌己灏戝己濂戠害缁戝畾锛屽彲鑳藉湪鎵嬪伐缂栬緫鍚庡紩鍏ラ潤榛橀敊璇€?- 鐮斿彂鍔熻兘锛?  - 鏂板 command guard gate锛屾牎楠?`command`/`command_parts` 鍙€嗕竴鑷存€э紙`shlex.split(command)` == `command_parts`锛変笌 canonical shell 瑙勮寖鍖栬緭鍑恒€?  - 鏍￠獙鑴氭湰鐩爣涓庡叧閿?flag 濂戠害锛?    - fan-out 蹇呴』鎸囧悜 `run_p2_linux_unified_execution_gate.py`锛屼笖鎼哄甫 `--report-dir/--shard-total/--shard-index`銆?    - fan-in aggregation 蹇呴』鎸囧悜 `run_p2_linux_shard_aggregation_gate.py`锛屼笖 `--summary` 椤哄簭涓ユ牸鍖归厤 `fan_in.summary_paths`銆?    - fan-in publish 蹇呴』鎸囧悜 `run_p2_linux_report_publish_gate.py`锛屼笖杈撳嚭璺緞涓?`fan_in` 瀛楁涓€鑷淬€?  - 鏀寔 `--write` 鍥炲啓 canonical command 瀛楃涓诧紝鏀舵暃璁″垝鏂囦欢鍛戒护鏍煎紡婕傜Щ銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_command_guard_gate.py`
  - `tests/test_p2_linux_ci_workflow_command_guard_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氬悎娉?workflow plan 蹇呴』閫氳繃 guard锛宍failed_commands=0`銆?  - `T2`锛歚command`/`command_parts` 涓嶄竴鑷存椂蹇呴』瑙﹀彂鎷掔粷锛屽苟缁欏嚭瑙勮寖鍖栧懡浠ゃ€?  - `T3`锛歛ggregation 鐨?`--summary` 椤哄簭涓?`fan_in.summary_paths` 涓嶄竴鑷存椂蹇呴』鎷掔粷銆?  - `T4`锛歱ublish 杈撳嚭璺緞涓?`fan_in.final_report_*` 涓嶄竴鑷存椂蹇呴』鎷掔粷銆?- 鍓嶇疆渚濊禆锛歚P2-19`

## P2-21 Linux CI Workflow 娌荤悊鏀舵暃闂ㄧ
- 鍗″彿锛歚P2-21`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-19` 涓?`P2-20` 宸插垎鍒鐩栤€滄覆鏌撴紓绉烩€濆拰鈥滃懡浠ゅ绾︹€濓紝浣嗙己灏戠粺涓€娌荤悊缁撹锛孋I 渚т粛闇€鎵嬪伐鎷兼帴澶氫唤鎶ュ憡鍒ゆ柇鏄惁鍙墽琛?workflow銆?  - 缂哄皯 metadata 琛€缂樹竴鑷存€ч棬绂侊紙`source_ci_workflow_plan` 涓?`workflow_output_path`锛夛紝瀛樺湪鈥滀骇鐗╃湅浼奸€氳繃銆佹潵婧愬凡閿欎綅鈥濈殑闅愭€ч闄┿€?- 鐮斿彂鍔熻兘锛?  - 鏂板 governance gate锛屼竴娆℃墽琛屾眹鎬?`workflow_sync + command_guard + metadata lineage` 涓夌被妫€鏌ワ紝浜у嚭鍗曚竴 `overall_status`銆?  - 杈撳嚭 `failed_checks` 鏄庣‘澶辫触绫诲埆锛歚workflow_sync_drift` / `command_guard_failed` / `lineage_mismatch`銆?  - 灏?`command_guard` 鎽樿鍖栦负 `failed_commands/issue_count/normalization_required`锛屼究浜?CI 鑱氬悎灞曠ず銆?  - 瀵?metadata 琛€缂樺仛寮烘牎楠岋細`source_ci_workflow_plan` 涓?`workflow_output_path` 蹇呴』涓庡綋鍓嶉棬绂佽緭鍏ヨ矾寰勪竴鑷淬€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_governance_gate.py`
  - `tests/test_p2_linux_ci_workflow_governance_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歸orkflow/command/lineage 鍏ㄩ儴涓€鑷存椂蹇呴』閫氳繃锛宍overall_status=passed`銆?  - `T2`锛歸orkflow YAML 婕傜Щ鏃跺繀椤昏惤鍏?`workflow_sync_drift` 澶辫触绫汇€?  - `T3`锛歝ommand 濂戠害寮傚父鏃跺繀椤昏惤鍏?`command_guard_failed` 澶辫触绫汇€?  - `T4`锛歮etadata 琛€缂樺瓧娈典笌杈撳叆璺緞涓嶄竴鑷存椂蹇呴』钀藉叆 `lineage_mismatch` 澶辫触绫汇€?- 鍓嶇疆渚濊禆锛歚P2-20`

## P2-22 Linux CI Workflow 娌荤悊鍙戝竷闂ㄧ
- 鍗″彿锛歚P2-22`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-21` 宸蹭骇鍑虹粺涓€娌荤悊缁撹锛屼絾 CI 涓嬫父浠嶉渶鎵嬪伐瑙ｆ瀽 `ci_workflow_governance.json` 鎵嶈兘鍐冲畾鈥滄槸鍚︽墽琛?workflow鈥濄€?  - 缂哄皯鍥哄畾鐨勫彂甯冧骇鐗╀笌 GitHub output 濂戠害锛屽鑷?fan-in 闃舵闅句互绋冲畾娑堣垂娌荤悊缁撴灉涓庡け璐ョ被鍒€?- 鐮斿彂鍔熻兘锛?  - 鏂板 governance publish gate锛岃鍙?`P2-21` 鎶ュ憡鍚庣敓鎴愬彲娑堣垂鍙戝竷浜х墿锛?    - `ci_workflow_governance_publish.json`
    - `ci_workflow_governance_publish.md`
  - 杈撳嚭绋冲畾鍐崇瓥瀛楁锛歚overall_status`銆乣should_execute_workflow`銆乣failed_checks`銆乣failed_check_count`銆?  - 鏀寔 `--github-output` 瀵煎嚭 CI 鍙橀噺锛歚governance_status`銆乣governance_should_execute_workflow`銆乣governance_failed_checks` 绛夈€?  - 澧炲姞鍙戝竷渚т竴鑷存€ф牎楠岋細鑻?`failed_checks` 鎴?`overall_status` 涓庨噸绠楃粨鏋滀笉涓€鑷达紝蹇呴』钀藉叆 `structural_issues` 骞跺垽瀹氬け璐ャ€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_governance_publish_gate.py`
  - `tests/test_p2_linux_ci_workflow_governance_publish_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氭不鐞嗘姤鍛婂叏閲忎竴鑷存椂搴旇緭鍑?`overall_status=passed` 涓?`should_execute_workflow=true`銆?  - `T2`锛氬綋娌荤悊鎶ュ憡鍖呭惈澶辫触妫€鏌ユ椂锛屽簲杈撳嚭 `overall_status=failed` 涓?`should_execute_workflow=false`銆?  - `T3`锛氬綋娌荤悊鎶ュ憡鐨?`failed_checks` 涓庨噸绠楃粨鏋滀笉涓€鑷存椂锛屽繀椤昏Е鍙?`structural_issues` 骞跺け璐ャ€?  - `T4`锛欸itHub output 瀵煎嚭瀛楁蹇呴』鍖呭惈鐘舵€併€佸け璐ュ垪琛ㄤ笌鍙戝竷浜х墿璺緞銆?- 鍓嶇疆渚濊禆锛歚P2-21`

## P2-23 Linux CI Workflow 鎵ц鍐崇瓥闂ㄧ
- 鍗″彿锛歚P2-23`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-22` 铏藉凡浜у嚭 `should_execute_workflow`锛屼絾 CI 涓嬫父浠嶇己鈥滅粺涓€鎵ц闂搁棬鈥濆皢娌荤悊缁撴灉杞垚鏄庣‘鐨?execute/blocked 缁撴灉涓庨€€鍑虹爜璇箟銆?  - 缂哄皯瀵规墽琛屽墠鍏抽敭浜х墿锛坵orkflow plan / rendered workflow锛夌殑瀛樺湪鎬ф牎楠岋紝鍙兘鍑虹幇鈥滄不鐞嗛€氳繃浣嗘墽琛屽叆鍙ｇ己澶扁€濈殑鏂摼銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 execution decision gate锛岃鍙?`P2-22` 鍙戝竷缁撴灉锛岀粺涓€杈撳嚭锛?    - `ci_workflow_execution_decision.json`
    - `ci_workflow_execution_decision.md`
  - 鍥哄寲鍐崇瓥瀛楁锛歚decision`銆乣decision_status`銆乣should_execute_workflow`銆乣exit_code`銆乣reason_codes`銆乣missing_artifacts`銆?  - 鏀寔闃绘柇绛栫暐寮€鍏筹細`--on-block fail|skip`锛岃 CI 鍙湪闃绘柇鏃堕€夋嫨 fail-fast 鎴?soft-skip銆?  - 鏀寔 `--github-output` 杈撳嚭涓嬫父鍙橀噺锛屽噺灏?job 闂存墜宸ヨВ鏋愩€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_decision_gate.py`
  - `tests/test_p2_linux_ci_workflow_decision_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氭不鐞嗛€氳繃涓旀墽琛屼骇鐗╅綈澶囨椂蹇呴』杈撳嚭 `decision=execute`銆乣exit_code=0`銆?  - `T2`锛氭不鐞嗗け璐ユ椂蹇呴』杈撳嚭 `decision=blocked` 涓旀惡甯﹀け璐ュ師鍥犵爜銆?  - `T3`锛氶樆鏂瓥鐣ヤ负 `skip` 鏃讹紝闃绘柇鍐崇瓥搴旇繑鍥?`exit_code=0`銆?  - `T4`锛欸itHub output 濂戠害闇€鍖呭惈 decision/status/should_execute/exit_code 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-22`

## P2-24 Linux CI Workflow 璋冨害灏辩华闂ㄧ
- 鍗″彿锛歚P2-24`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-23` 宸蹭骇鍑?execute/blocked 鍐崇瓥锛屼絾 CI 涓嬫父浠嶉渶鎵嬪伐灏嗗喅绛栧瓧娈垫嫾瑁呬负瀹為檯璋冨害鍛戒护锛屽瓨鍦ㄥ懡浠や笉涓€鑷翠笌閿欒瑙﹀彂椋庨櫓銆?  - 缂哄皯缁熶竴 dispatch 濂戠害鎶ュ憡锛屽鑷粹€滄槸鍚﹀彲鍙戣捣 `gh workflow run`鈥濈殑鍒ゆ柇鏃犳硶琚?job 闂寸ǔ瀹氬鐢ㄣ€?- 鐮斿彂鍔熻兘锛?  - 鏂板 dispatch readiness gate锛岃鍙?`P2-23` 鍐崇瓥浜х墿骞惰緭鍑猴細
    - `ci_workflow_dispatch.json`
    - `ci_workflow_dispatch.md`
  - 鍥哄寲璋冨害瀛楁锛歚dispatch_status`銆乣dispatch_mode`銆乣should_dispatch_workflow`銆乣dispatch_command`銆乣dispatch_command_parts`銆?  - execute 鍐崇瓥鏃剁敓鎴愯鑼冨寲 `gh workflow run` 鍛戒护锛沚locked 鍐崇瓥鏃惰緭鍑虹┖鍛戒护骞朵繚鎸侀樆鏂師鍥犲彲杩芥函銆?  - 鏀寔 `--github-output` 瀵煎嚭 dispatch 鐘舵€併€佸懡浠や笌鎶ュ憡璺緞锛屼緵涓嬫父 CI 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_dispatch_gate.py`
  - `tests/test_p2_linux_ci_workflow_dispatch_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歟xecute 鍐崇瓥鏃跺繀椤讳骇鍑?`dispatch_status=ready` 涓庡悎娉?`gh workflow run` 鍛戒护銆?  - `T2`锛歜locked 鍐崇瓥鏃跺繀椤讳骇鍑?`dispatch_status=blocked` 涓?`dispatch_command` 涓虹┖銆?  - `T3`锛氬喅绛栧绾﹀啿绐侊紙濡?decision=execute 浣?should_execute=false锛夋椂蹇呴』鎷掔粷銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈 dispatch 鐘舵€併€佽皟搴﹀懡浠や笌鎶ュ憡璺緞銆?- 鍓嶇疆渚濊禆锛歚P2-23`

## P2-25 Linux CI Workflow 璋冨害鎵ц闂ㄧ
- 鍗″彿锛歚P2-25`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-24` 浠呬骇鍑衡€滃彲璋冨害濂戠害鈥濓紝鏈粺涓€澶勭悊鐪熸 dispatch 鎵ц缁撴灉锛孋I 涓嬫父浠嶉渶閲嶅鎷兼帴鈥滄槸鍚︽墽琛?鎵ц澶辫触濡備綍鍥炴姤鈥濈殑閫昏緫銆?  - 缂哄皯璋冨害鎵ц灞傜粺涓€鎶ュ憡锛屽鑷?execute/blocked/fail 涓夋€佹棤娉曠ǔ瀹氭矇娣€涓哄崟涓€瀹¤浜х墿銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 dispatch execution gate锛岃鍙?`P2-24` 璋冨害濂戠害骞惰緭鍑猴細
    - `ci_workflow_dispatch_execution.json`
    - `ci_workflow_dispatch_execution.md`
  - 鍥哄寲鎵ц瀛楁锛歚execution_status`銆乣execution_exit_code`銆乣dispatch_attempted`銆乣command_returncode`銆乣reason_codes`銆?  - `dispatch_status=ready` 鏃舵墽琛?`dispatch_command_parts`锛堟敮鎸?`--dry-run` 璺宠繃鐪熷疄鎵ц锛夛紱`dispatch_status=blocked` 鏃朵繚鎸佹棤鎵ц浣嗕繚鐣欓樆鏂涔夈€?  - 鏀寔 `--github-output` 瀵煎嚭鎵ц鐘舵€併€侀€€鍑虹爜涓庢姤鍛婅矾寰勶紝渚?Linux CI 涓嬫父 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_dispatch_execution_gate.py`
  - `tests/test_p2_linux_ci_workflow_dispatch_execution_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歳eady + dry-run 蹇呴』浜у嚭 `execution_status=ready_dry_run` 涓?`execution_exit_code=0`銆?  - `T2`锛歜locked 鍐崇瓥蹇呴』淇濇寔 `dispatch_attempted=false` 涓旈€€鍑虹爜閬靛惊涓婃父闃绘柇绛栫暐璇箟銆?  - `T3`锛歞ispatch 濂戠害鍐茬獊锛堝 command 涓?command_parts 涓嶄竴鑷达級蹇呴』鎷掔粷銆?  - `T4`锛氬懡浠ゆ墽琛屽け璐ユ椂蹇呴』钀藉湴 `execution_status=dispatch_failed` 骞舵惡甯﹀け璐ュ師鍥犵爜銆?  - `T5`锛欸itHub output 濂戠害闇€鍖呭惈鎵ц鐘舵€併€佹槸鍚﹀皾璇曡皟搴︺€侀€€鍑虹爜涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-24`

## P2-26 Linux CI Workflow 鍏ㄩ摼缂栨帓闂ㄧ
- 鍗″彿锛歚P2-26`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-17` 鑷?`P2-33` 鍚勯棬绂佸凡鍏峰锛屼絾 CI 渚т粛闇€浜哄伐鎷兼帴澶氭潯鍛戒护锛屽鏄撳嚭鐜伴樁娈甸仐婕忋€佸弬鏁版紓绉讳笌椤哄簭閿欒銆?  - 缂哄皯鈥滃崟鍏ュ彛鈥濋棬绂佺粺涓€璋冨害 workflow plan/yaml/sync/governance/dispatch/terminal publish 鍏ㄩ摼锛屽鑷?Linux CI 缂栨帓閲嶅缁存姢鎴愭湰楂樸€?- 鐮斿彂鍔熻兘锛?  - 鏂板 full pipeline gate锛屼竴娆＄紪鎺?`P2-17 -> P2-33` 鍗佸叚闃舵锛?    - plan -> yaml -> sync -> command_guard -> governance -> governance_publish -> decision -> dispatch -> dispatch_execution -> dispatch_trace -> dispatch_completion -> terminal_publish -> release_handoff -> release_trigger -> release_trace -> release_completion銆?  - 鏀寔缁熶竴闃舵瑁佸壀 `--skip-*`锛屽厑璁稿湪 CI fan-in / rerun 鍦烘櫙鎸夐渶璺宠繃鍓嶅簭闃舵銆?  - 鏀寔缁熶竴绛栫暐閫忎紶锛歚--strict-generated-at`銆乣--sync-write`銆乣--command-guard-write`銆乣--on-block`銆乣--workflow-ref`銆乣--dispatch-timeout-seconds`銆乣--dispatch-trace-poll-now`銆乣--completion-allow-in-progress`銆?  - 鏀寔 `--print-commands/--dry-run` 棰勮涓?`--fail-fast` 鎵ц绛栫暐锛屾矇娣€鍗曚竴 Linux CI 缂栨帓鍏ュ彛銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛氶粯璁ら樁娈甸摼蹇呴』瀹屾暣瑕嗙洊 `P2-17 -> P2-33` 涓旈『搴忓浐瀹氥€?  - `T2`锛氱瓥鐣ュ弬鏁帮紙strict/sync-write/command-guard-write/on-block/workflow-ref/timeout/trace-poll锛夊繀椤绘纭€忎紶鍒板搴斿瓙闂ㄧ銆?  - `T3`锛氶儴鍒?`--skip-*` 鏃跺繀椤诲彧淇濈暀鍚庡崐閾鹃樁娈靛苟淇濇寔椤哄簭銆?  - `T4`锛氬叏閮?`--skip-*` 鏃跺簲杩斿洖绌鸿鍒掞紙涓嶈Е鍙戦樁娈垫墽琛岋級銆?  - `T5`锛氭敮鎸佷粎缁堝眬鍙戝竷闃舵锛坄terminal_publish`锛変笌 release completion 闃舵鐙珛鎵ц銆?- 鍓嶇疆渚濊禆锛歚P2-25`

## P2-27 Linux CI Workflow 璋冨害杩借釜闂ㄧ
- 鍗″彿锛歚P2-27`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-25` 鍙鐩?dispatch 鍛戒护鎵ц鍥炴墽锛屼絾鏈敹鏁?workflow run 鐨勮拷韪绾︼紝CI 涓嬫父浠嶉渶鎵嬪伐瑙ｆ瀽鏃ュ織鎻愬彇 `run_id`/`run_url`銆?  - 缂哄皯缁熶竴 run poll 鍛戒护涓庤拷韪姸鎬侊紝瀵艰嚧鍚庣画 job 瀵光€滃凡璋冨害浣嗘湭瀹屾垚鈥濈殑鐘舵€佸垽鏂笉涓€鑷淬€?- 鐮斿彂鍔熻兘锛?  - 鏂板 dispatch trace gate锛岃鍙?`P2-25` 鎵ц鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_dispatch_trace.json`
    - `ci_workflow_dispatch_trace.md`
  - 浠?dispatch stdout/stderr 鎻愬彇 canonical GitHub Actions run URL 涓?`run_id`锛岀敓鎴愬彲澶嶇敤 poll 鍛戒护锛坄gh run view <run_id> --json ...`锛夈€?  - 鏀寔 `--poll-now` 绔嬪嵆鎵ц涓€娆?run 鐘舵€佹煡璇紝缁熶竴 `run_tracking_ready` / `run_in_progress` / `run_completed_success` / `run_completed_failure` / `run_poll_failed` 鍒ゅ畾銆?  - 鏀寔 `--github-output` 瀵煎嚭杩借釜鐘舵€併€乺un 鏍囪瘑銆乸oll 缁撴灉涓庢姤鍛婅矾寰勶紝渚?CI 涓嬫父鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_dispatch_trace_gate.py`
  - `tests/test_p2_linux_ci_workflow_dispatch_trace_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚dispatched` 涓斿惈 run URL 鏃跺繀椤绘彁鍙?`run_id/run_url` 骞剁敓鎴?poll 鍛戒护銆?  - `T2`锛歚dispatched` 浣嗙己 run URL 鏃跺繀椤昏惤鍏?`run_tracking_missing` 涓旇繑鍥炲け璐ラ€€鍑虹爜銆?  - `T3`锛歚blocked`/`ready_dry_run` 璺緞蹇呴』淇濇寔鏃?poll 灏濊瘯骞堕€忎紶涓婃父璇箟銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈杩借釜鐘舵€併€乺un_id/run_url銆佹姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-26`
## P2-28 Linux CI Workflow 璋冨害瀹屾垚鏀舵暃闂ㄧ
- 鍗″彿锛歚P2-28`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-27` 浠呮彁渚涘崟娆?trace 涓庡彲閫夊崟娆?poll锛屾湭鎻愪緵鈥滅瓑寰呰嚦缁堟€佲€濈殑缁熶竴鏀舵暃濂戠害锛汣I 涓嬫父浠嶉渶鑷寰幆 `gh run view` 骞跺鐞嗚秴鏃?杩涜涓?澶辫触鍒嗘敮銆?  - 缂哄皯缁熶竴 completion verdict锛屽鑷?`run_in_progress`銆乣run_completed_failure`銆乣run_poll_failed`銆乣run_tracking_missing` 鍦ㄤ笉鍚?job 涓€€鍑鸿涔変笉涓€鑷淬€?- 鐮斿彂鍔熻兘锛?  - 鏂板 dispatch completion gate锛岃鍙?`P2-27` trace 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_dispatch_completion.json`
    - `ci_workflow_dispatch_completion.md`
  - 鏀寔杞绛夊緟鍙傛暟锛歚--poll-interval-seconds`銆乣--max-polls`銆乣--poll-timeout-seconds`锛屽皢 run 鐘舵€佺粺涓€鏀舵暃涓猴細
    - `run_completed_success`
    - `run_completed_failure`
    - `run_poll_failed`
    - `run_await_timeout`
    - 浠ュ強閫忎紶鍨?`blocked` / `ready_dry_run` / `run_tracking_missing`
  - 鎻愪緵 `--allow-in-progress` 绛栫暐寮€鍏筹細瓒呮椂浠?in-progress 鏃跺彲閫夋槸鍚﹁繑鍥?exit 0锛屾弧瓒充笉鍚?CI 缂栨帓绛栫暐銆?  - 鏀寔 `--github-output` 瀵煎嚭 completion 鐘舵€併€乸oll 杩唬銆乺un_id/url銆佹姤鍛婅矾寰勶紝渚?Linux CI 涓嬫父 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_dispatch_completion_gate.py`
  - `tests/test_p2_linux_ci_workflow_dispatch_completion_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚run_tracking_ready` 涓?poll 杩斿洖 completed+success 鏃讹紝蹇呴』鏀舵暃涓?`run_completed_success` 涓?`completion_exit_code=0`銆?  - `T2`锛氭寔缁?in-progress 鍒?`max_polls` 鍚庯紝蹇呴』钀?`run_await_timeout`锛屽苟鎸?`--allow-in-progress` 鍐冲畾閫€鍑虹爜銆?  - `T3`锛歵race 涓?`poll_command` 涓?`poll_command_parts` 涓嶄竴鑷存椂蹇呴』鎷掔粷銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈 completion 鐘舵€併€乪xit code銆乸oll 娆℃暟銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-27`

## P2-29 Linux CI Workflow 缁堝眬鍙戝竷闂ㄧ
- 鍗″彿锛歚P2-29`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-28` 宸茬粰鍑?completion verdict锛屼絾涓嬫父鍙戝竷娴佺▼浠嶉渶鑷灏?`completion_status` 鏄犲皠涓哄彲鍙戝竷璇箟锛坧romote/hold/fail锛夛紝瀵艰嚧鏀跺彛绛栫暐涓嶄竴鑷淬€?  - 缂哄皯缁熶竴缁堝眬 publish 濂戠害锛岄毦浠ョǔ瀹氬鐢ㄥ湪 release gate 涓庡悗缁幆澧冩帹骞跨瓥鐣ヤ腑銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 terminal publish gate锛岃鍙?`P2-28` completion 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_terminal_publish.json`
    - `ci_workflow_terminal_publish.md`
  - 灏?completion 璇箟缁熶竴鏀舵暃涓?`publish_status`锛坄passed`/`blocked`/`in_progress`/`failed`/`contract_failed`锛変笌 `should_promote`銆?  - 鍥哄寲濂戠害涓€鑷存€ф牎楠岋紙濡?`run_completed_success` 蹇呴』 `completion_exit_code=0`锛夛紝涓嶄竴鑷存椂钀?`contract_failed`銆?  - 鏀寔 `--github-output` 瀵煎嚭缁堝眬鐘舵€併€乸romote 鍐崇瓥銆乺un 鏍囪瘑涓庢姤鍛婅矾寰勶紝渚?Linux CI 涓嬫父 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_terminal_publish_gate.py`
  - `tests/test_p2_linux_ci_workflow_terminal_publish_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚run_completed_success` + `completion_exit_code=0` 鏃跺繀椤绘敹鏁涗负 `publish_status=passed` 涓?`should_promote=true`銆?  - `T2`锛歚run_await_timeout` + `allow_in_progress=true` 鏃跺繀椤绘敹鏁涗负 `publish_status=in_progress` 涓?`publish_exit_code=0`銆?  - `T3`锛歝ompletion 濂戠害涓嶄竴鑷达紙濡?success 浣?exit_code 闈?0锛夋椂蹇呴』鏀舵暃涓?`publish_status=contract_failed`銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈缁堝眬鐘舵€併€乸romote 鍐崇瓥銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-28`

## P2-30 Linux CI Workflow Release Handoff Gate
- 鍗″彿锛歚P2-30`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-29` 宸茬粰鍑?publish verdict锛屼絾 release job 浠嶉渶鑷瑙ｆ瀽 `publish_status/should_promote` 缁勮瑙﹀彂鏉′欢锛屽鑷存帹骞胯涔夊垎鍙夈€?  - 缂哄皯缁熶竴 handoff 濂戠害锛屼笉鍒╀簬鍚庣画閮ㄧ讲骞冲彴鎴栧鎵规祦澶嶇敤 Linux CI 缁堝眬缁撹銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 release handoff gate锛岃鍙?`P2-29` terminal publish 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_handoff.json`
    - `ci_workflow_release_handoff.md`
  - 灏?publish 璇箟缁熶竴鏀舵暃涓?`handoff_status`锛坄ready_for_release`/`awaiting_completion`/`blocked`/`failed`/`contract_failed`锛変笌 `should_trigger_release`銆?  - 鍥哄寲濂戠害涓€鑷存€ф牎楠岋紙濡?`publish_status=passed` 蹇呴』 `publish_exit_code=0` 涓?`should_promote=true`锛夛紝涓嶄竴鑷存椂钀?`contract_failed`銆?  - 鏀寔 `--target-environment`銆乣--release-channel` 閫忎紶鍙戝竷鐩爣璇箟锛屽苟鏀寔 `--github-output` 瀵煎嚭 handoff 鐘舵€併€乺elease action銆乺un 鏍囪瘑涓庢姤鍛婅矾寰勩€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_handoff_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_handoff_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚publish_status=passed` + `should_promote=true` 鏃跺繀椤绘敹鏁涗负 `handoff_status=ready_for_release` 涓?`should_trigger_release=true`銆?  - `T2`锛歚publish_status=in_progress` 鏃跺繀椤绘敹鏁涗负 `handoff_status=awaiting_completion` 涓?`release_exit_code=0`銆?  - `T3`锛歵erminal publish 濂戠害鍐茬獊锛堝 passed 浣?should_promote=false锛夋椂蹇呴』鏀舵暃涓?`handoff_status=contract_failed`銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈 handoff 鐘舵€併€乺elease action銆乼arget env/channel銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-29`

## P2-31 Linux CI Workflow Release Trigger Gate
- 鍗″彿锛歚P2-31`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-30` 宸蹭骇鍑?`should_trigger_release` 璇箟锛屼絾浠嶇己灏戔€滅湡姝ｆ墽琛?release dispatch鈥濈殑缁熶竴鎵ц闂ㄧ锛汣I 涓嬫父闇€鑷鎷艰鍛戒护骞跺鐞嗚秴鏃?澶辫触鍒嗘敮锛岃Е鍙戣涓轰笉涓€鑷淬€?  - 缂哄皯缁熶竴 trigger 鎵ц鎶ュ憡锛屼笉鍒╀簬鍚庣画 release 杩借釜銆佸洖婧笌瀹¤銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 release trigger gate锛岃鍙?`P2-30` release handoff 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_trigger.json`
    - `ci_workflow_release_trigger.md`
  - 褰?`should_trigger_release=true` 鏃讹紝鑷姩鏋勫缓骞舵墽琛?release dispatch command锛堟敮鎸佽嚜瀹氫箟 `--release-command` 瑕嗙洊榛樿鍛戒护锛夈€?  - 褰?`should_trigger_release=false` 鏃讹紝鎸?handoff 鐘舵€佹敹鏁涗负 `release_trigger_status`锛坄awaiting_completion`/`blocked`/`handoff_failed`锛夛紝骞朵繚鎸侀浂瑙﹀彂鍓綔鐢ㄣ€?  - 鍥哄寲濂戠害鏍￠獙锛歨andoff 鐘舵€併€乤ction銆乪xit code 涓庤Е鍙戝竷灏斿€煎繀椤讳竴鑷达紱涓嶄竴鑷村嵆鎷掔粷鎵ц銆?  - 鏀寔 `--github-output` 瀵煎嚭 trigger 鐘舵€併€佽Е鍙戝皾璇曘€乪xit code銆乺un 鏍囪瘑涓庢姤鍛婅矾寰勩€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_trigger_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_trigger_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚ready_for_release + should_trigger_release=true` 鍦?dry-run 璺緞蹇呴』鏀舵暃涓?`release_trigger_status=ready_dry_run`銆?  - `T2`锛歚awaiting_completion` 璺緞蹇呴』淇濇寔 `release_trigger_status=awaiting_completion` 涓斾笉瑙﹀彂鍛戒护鎵ц銆?  - `T3`锛歨andoff 濂戠害鍐茬獊锛堝 `ready_for_release` 浣?`should_trigger_release=false`锛夊繀椤昏鎷掔粷鍔犺浇銆?  - `T4`锛氳Е鍙戝懡浠ら潪闆惰繑鍥炲繀椤绘敹鏁涗负 `release_trigger_status=trigger_failed` 骞惰褰曞け璐?reason code銆?  - `T5`锛欸itHub output 濂戠害蹇呴』鍖呭惈 trigger 鐘舵€併€乤ttempted銆乪xit code銆乪nv/channel銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-30`

## P2-32 Linux CI Workflow Release Traceability Gate
- 鍗″彿锛歚P2-32`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-31` 宸插畬鎴?release trigger 鎵ц锛屼絾缂哄皯 release run 杩借釜濂戠害锛涗笅娓?job 闇€瑕侀噸澶嶈В鏋?stdout/stderr 鎵嶈兘鎷垮埌 `run_id/run_url`锛岃拷韪涔変笉涓€鑷淬€?  - 缂哄皯缁熶竴 release trace 鎶ュ憡锛屼笉鍒╀簬鍚庣画 release 瀹屾垚鎬佹敹鏁涖€佸璁¤拷婧笌璺?job 澶嶇敤銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 release trace gate锛岃鍙?`P2-31` release trigger 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_trace.json`
    - `ci_workflow_release_trace.md`
  - 褰?`release_trigger_status=triggered` 鏃讹紝缁熶竴鎻愬彇 release run 寮曠敤骞舵敹鏁涗负锛?    - `release_run_id` / `release_run_url`
    - `release_tracking_status`锛坄release_run_tracking_ready`/`release_run_tracking_missing`锛?    - 鍙€?poll 鍛戒护濂戠害锛坄release_poll_command` + `release_poll_command_parts`锛?  - 鏀寔 `--poll-now` 绔嬪嵆鏌ヨ release run 鐘舵€侊紝鏀舵暃涓猴細
    - `release_run_in_progress` / `release_run_completed_success` / `release_run_completed_failure` / `release_run_poll_failed`
  - 瀵归潪瑙﹀彂鐘舵€侊紙`ready_dry_run` / `awaiting_completion` / `blocked` / `handoff_failed` / `trigger_failed`锛夌粺涓€閫忎紶鎴愭棤鍓綔鐢?trace 璇箟銆?  - 鏀寔 `--github-output` 瀵煎嚭 trace 鐘舵€併€乻hould_poll銆乺un_id/url銆乸oll 鐘舵€佷笌鎶ュ憡璺緞銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_trace_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_trace_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚triggered` 鎶ュ憡蹇呴』鎻愬彇鍑?run 寮曠敤锛屽苟鏀舵暃涓?`release_tracking_status=release_run_tracking_ready`銆?  - `T2`锛歚triggered` 浣嗙己灏?run 寮曠敤鏃跺繀椤绘敹鏁涗负 `release_tracking_status=release_run_tracking_missing` 涓?`release_trace_exit_code=1`銆?  - `T3`锛歚trigger_failed` 璺緞蹇呴』閫忎紶涓?`release_tracking_status=release_trigger_failed` 涓斾笉瑙﹀彂 poll銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈 trace 鐘舵€併€乻hould_poll銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-31`

## P2-33 Linux CI Workflow Release Completion Gate
- 鍗″彿锛歚P2-33`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-32` 宸插叿澶?release run trace 濂戠害锛屼絾鈥滅瓑寰?run 瀹屾垚鈥濅粛闇€涓嬫父 job 鑷杞锛岀己灏戠粺涓€瀹屾垚鎬佹敹鏁涖€?  - 鏃犵粺涓€ release completion 鎶ュ憡锛屽鑷?release 鎴愬姛/澶辫触/瓒呮椂/杩涜涓殑鏈€缁堣涔夊湪 CI 鍚勯樁娈典笉涓€鑷淬€?- 鐮斿彂鍔熻兘锛?  - 鏂板 release completion gate锛岃鍙?`P2-32` release trace 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_completion.json`
    - `ci_workflow_release_completion.md`
  - 鏀寔 bounded poll loop锛歚--poll-interval-seconds`銆乣--max-polls`銆乣--poll-timeout-seconds`銆?  - 鏀舵暃 completion_status锛?    - `release_run_completed_success`
    - `release_run_completed_failure`
    - `release_run_in_progress`
    - `release_run_await_timeout`
    - `release_run_poll_failed`
    - 鍙?blocked/dry-run/trigger_failed 绛夐€忎紶鐘舵€併€?  - 鏀寔 `--allow-in-progress`锛氬厑璁歌秴鏃朵粛 in-progress 鏃惰繑鍥?exit 0銆?  - 鏀寔 `--github-output` 瀵煎嚭 completion 鐘舵€併€佽疆璇俊鎭€乺un_id/url 涓庢姤鍛婅矾寰勩€?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_completion_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_completion_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚release_run_tracking_ready` + poll success 蹇呴』鏀舵暃涓?`release_run_completed_success`銆?  - `T2`锛氭寔缁?in-progress 涓旀湭鍏佽 in-progress 蹇呴』鏀舵暃涓?`release_run_await_timeout` 涓旈€€鍑虹爜闈為浂銆?  - `T3`锛歳elease poll command 涓?parts 涓嶄竴鑷存椂蹇呴』鎷掔粷鍔犺浇銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈 completion 鐘舵€併€乸oll 淇℃伅銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-32`

## P2-34 Linux CI Workflow Release Terminal Publish Gate
- 鍗″彿锛歚P2-34`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-33` 宸茬粰鍑?release completion verdict锛屼絾涓嬫父 release 鏈€缁堟敹鍙ｄ粛闇€鑷瑙ｆ瀽 completion 璇箟锛屽鏄撲骇鐢?finalize/hold/fail 鍒ゅ畾婕傜Щ銆?  - 缂哄皯缁熶竴 release terminal publish 濂戠害锛屼笉鍒╀簬鍚庣画 release governance 涓庣幆澧冩帹杩涚瓥鐣ュ鐢ㄣ€?- 鐮斿彂鍔熻兘锛?  - 鏂板 release terminal publish gate锛岃鍙?`P2-33` release completion 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_terminal_publish.json`
    - `ci_workflow_release_terminal_publish.md`
  - 灏?release completion 璇箟缁熶竴鏀舵暃涓?`release_publish_status`锛坄passed`/`blocked`/`in_progress`/`failed`/`contract_failed`锛変笌 `should_finalize_release`銆?  - 鍥哄寲濂戠害涓€鑷存€ф牎楠岋紙濡?`release_run_completed_success` 蹇呴』 `release_completion_exit_code=0`锛夛紝涓嶄竴鑷存椂钀?`contract_failed`銆?  - 鏀寔 `--github-output` 瀵煎嚭 release terminal 鐘舵€併€乫inalize 鍐崇瓥銆乺un_id/url 涓庢姤鍛婅矾寰勶紝渚夸簬 Linux CI 涓嬫父 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_terminal_publish_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_terminal_publish_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚release_run_completed_success` + `release_completion_exit_code=0` 鏃跺繀椤绘敹鏁涗负 `release_publish_status=passed` 涓?`should_finalize_release=true`銆?  - `T2`锛歚release_run_await_timeout` + `allow_in_progress=true` 鏃跺繀椤绘敹鏁涗负 `release_publish_status=in_progress` 涓?`release_publish_exit_code=0`銆?  - `T3`锛歝ompletion 濂戠害涓嶄竴鑷达紙濡?success 浣?exit_code 闈?0锛夋椂蹇呴』鏀舵暃涓?`release_publish_status=contract_failed`銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈 release terminal 鐘舵€併€乫inalize 鍐崇瓥銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-33`

## P2-35 Linux CI Workflow Release Finalization Gate
- 鍗″彿锛歚P2-35`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-34` 宸茶緭鍑?release terminal publish verdict锛屼絾鈥滄渶缁堟槸鍚︽敹鍙?release 鐢熷懡鍛ㄦ湡鈥濈殑绛栫暐浠嶅垎鏁ｅ湪涓嬫父 job锛屽鏄撳嚭鐜?finalize/hold/abort 鍒ゅ畾婕傜Щ銆?  - 缂哄皯缁熶竴 finalization 濂戠害锛屼笉鍒╀簬 Linux CI 鍦ㄧ粓鐐归樁娈电粰鍑虹ǔ瀹氱殑 release closure 缁撴灉涓庡彲瀹¤鍑哄彛銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 release finalization gate锛岃鍙?`P2-34` release terminal publish 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_finalization.json`
    - `ci_workflow_release_finalization.md`
  - 灏?release terminal publish 璇箟缁熶竴鏀舵暃涓猴細
    - `release_finalization_status`锛坄finalized` / `awaiting_release` / `failed` / `contract_failed`锛?    - `release_finalization_decision`锛坄finalize` / `hold` / `abort`锛?    - `release_finalization_exit_code`
  - 鏀寔 `--on-hold` 绛栫暐锛坄pass`/`fail`锛夋帶鍒?blocked/in_progress 鏀跺彛閫€鍑虹爜璇箟銆?  - 鍥哄寲濂戠害涓€鑷存€ф牎楠岋紙濡?`release_publish_status=passed` 蹇呴』 `release_publish_exit_code=0` 涓?`should_finalize_release=true`锛夛紝涓嶄竴鑷存椂寮哄埗 `contract_failed`銆?  - 鏀寔 `--github-output` 瀵煎嚭 finalization 鐘舵€併€佸喅绛栥€乺un_id/url 涓庢姤鍛婅矾寰勶紝渚?Linux CI 涓嬫父 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_finalization_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_finalization_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚release_publish_status=passed` + 濂戠害涓€鑷存椂蹇呴』鏀舵暃涓?`release_finalization_status=finalized` 涓?`should_finalize_release=true`銆?  - `T2`锛歚release_publish_status=in_progress` 涓?`--on-hold=fail` 鏃跺繀椤绘敹鏁涗负 `release_finalization_status=awaiting_release` 涓旈€€鍑虹爜闈?0銆?  - `T3`锛歵erminal publish 濂戠害涓嶄竴鑷达紙濡?passed 浣?exit_code 闈?0锛夋椂蹇呴』鏀舵暃涓?`release_finalization_status=contract_failed`銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈 finalization 鐘舵€併€佸喅绛栥€乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-34`

## P2-36 Linux CI Workflow Release Closure Publish Gate
- 鍗″彿锛歚P2-36`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-35` 宸茶緭鍑?finalization verdict锛屼絾瀵瑰娑堣垂锛堥€氱煡銆佸綊妗ｃ€佷笅娓哥郴缁熸帴鍏ワ級浠嶉渶鑷鎷兼帴瀛楁锛宑losure 璇箟瀹规槗鍑虹幇 close/hold/rollback 鍒ゅ畾婕傜Щ銆?  - 缂哄皯缁熶竴 release closure 鍙戝竷濂戠害锛屼笉鍒╀簬 Linux CI 鍦ㄧ粓鐐归樁娈靛澶栨彁渚涚ǔ瀹氬崟鍑哄彛锛坢achine-readable + human-readable锛夌粨鏋溿€?- 鐮斿彂鍔熻兘锛?  - 鏂板 release closure gate锛岃鍙?`P2-35` release finalization 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_closure.json`
    - `ci_workflow_release_closure.md`
  - 灏?finalization 璇箟缁熶竴鏀舵暃涓猴細
    - `release_closure_status`锛坄closed` / `pending` / `failed` / `contract_failed`锛?    - `release_closure_decision`锛坄ship` / `hold` / `rollback`锛?    - `release_closure_exit_code`
    - `should_close_release` 涓?`should_notify`
  - 鍥哄寲 finalization 濂戠害涓€鑷存€ф牎楠岋紙濡?`release_finalization_status=finalized` 蹇呴』 `release_finalization_decision=finalize` 涓?`release_finalization_exit_code=0`锛夛紝涓嶄竴鑷存椂寮哄埗 `contract_failed`銆?  - 鏀寔 `--github-output` 瀵煎嚭 closure 鐘舵€併€佸喅绛栥€乺un_id/url 涓庢姤鍛婅矾寰勶紝渚?Linux CI 涓嬫父 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_closure_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_closure_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚release_finalization_status=finalized` + 濂戠害涓€鑷存椂蹇呴』鏀舵暃涓?`release_closure_status=closed` 涓?`release_closure_decision=ship`銆?  - `T2`锛歚release_finalization_status=awaiting_release` 鏃跺繀椤绘敹鏁涗负 `release_closure_status=pending` 涓斾繚鎸?hold 璇箟銆?  - `T3`锛歠inalization 濂戠害涓嶄竴鑷达紙濡?finalized 浣?decision!=finalize锛夋椂蹇呴』鏀舵暃涓?`release_closure_status=contract_failed`銆?  - `T4`锛欸itHub output 濂戠害蹇呴』鍖呭惈 closure 鐘舵€併€佸喅绛栥€乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-35`

## P2-37 Linux CI Workflow Release Archive Publish Gate
- 鍗″彿锛歚P2-37`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-36` 宸茶緭鍑?release closure verdict锛屼絾 release evidence锛坈losure/finalization/trace/dispatch source artifacts锛変粛鏈舰鎴愮粺涓€ machine-readable 褰掓。濂戠害銆?  - 缂哄皯缁堢偣褰掓。鍗曞嚭鍙ｆ椂锛孡inux CI 涓嬫父锛堥€氱煡銆佸璁°€佸綊妗ｇ郴缁燂級浠嶉渶鑷鎷兼帴璺緞涓庡垽瀹氾紝瀛樺湪鍙戝竷缁撹涓庤瘉鎹紓绉婚闄┿€?- 鐮斿彂鍔熻兘锛?  - 鏂板 release archive gate锛岃鍙?`P2-36` release closure 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_archive.json`
    - `ci_workflow_release_archive.md`
  - 灏?closure 璇箟缁熶竴鏀舵暃涓猴細
    - `release_archive_status`锛坄ready` / `pending` / `failed` / `contract_failed`锛?    - `release_archive_decision`锛坄publish` / `hold` / `block`锛?    - `release_archive_exit_code`
    - `should_publish_archive`
  - 鏋勫缓 evidence manifest锛堝寘鍚?closure 涓庡叾涓婃父 source_* 鎶ュ憡璺緞瀛樺湪鎬э級锛屽彂鐜扮己澶卞嵆寮哄埗 `contract_failed`銆?  - 鏀寔 `--github-output` 瀵煎嚭 archive 鐘舵€併€佸喅绛栥€乵issing artifacts 涓庢姤鍛婅矾寰勶紝渚?Linux CI 涓嬫父 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_archive_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_archive_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚release_closure_status=closed` 涓?evidence 瀹屾暣鏃跺繀椤绘敹鏁涗负 `release_archive_status=ready` 涓?`release_archive_decision=publish`銆?  - `T2`锛歚release_closure_status=pending` 鏃跺繀椤绘敹鏁涗负 `release_archive_status=pending` 涓斾繚鎸?hold 璇箟銆?  - `T3`锛歝losure 濂戠害涓嶄竴鑷达紙濡?closed 浣?decision!=ship锛夋椂蹇呴』鏀舵暃涓?`release_archive_status=contract_failed`銆?  - `T4`锛歟vidence 缂哄け鏃跺繀椤绘爣璁?missing artifacts 骞舵敹鏁涗负 `contract_failed`銆?  - `T5`锛欸itHub output 濂戠害蹇呴』鍖呭惈 archive 鐘舵€併€佸喅绛栥€乺un_id/url銆乵issing artifacts 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-36`

## P2-38 Linux CI Workflow Release Verdict Publish Gate
- 鍗″彿锛歚P2-38`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-37` 宸茶緭鍑?release archive verdict锛屼絾 Linux CI 缁堢偣浠嶇己灏戠粺涓€鈥滄槸鍚︽斁琛屽彂甯冣€濈殑鍗曞嚭鍙ｅ垽璇嶏紝缁堟€?ship/hold/block 璇箟鍒嗘暎鍦ㄥ瀛楁涓€?  - 缂哄皯鏈€缁?verdict 濂戠害鏃讹紝涓嬫父娴佹按绾夸笌鍙戝竷鐪嬫澘浠嶉渶鑷鎷艰鍒ゅ畾閫昏緫锛屽瓨鍦ㄥ嚭鍙ｈ涔夋紓绉婚闄┿€?- 鐮斿彂鍔熻兘锛?  - 鏂板 release verdict gate锛岃鍙?`P2-37` release archive 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_verdict.json`
    - `ci_workflow_release_verdict.md`
  - 灏?archive 璇箟缁熶竴鏀舵暃涓猴細
    - `release_verdict_status`锛坄published` / `awaiting_archive` / `blocked` / `contract_failed`锛?    - `release_verdict_decision`锛坄ship` / `hold` / `block`锛?    - `release_verdict_exit_code`
    - `should_ship_release` 涓?`should_open_incident`
  - 鍥哄寲 archive 濂戠害涓€鑷存€ф牎楠岋紙濡?`release_archive_status=ready` 蹇呴』 `release_archive_decision=publish` 涓?`release_archive_exit_code=0`锛夛紝涓嶄竴鑷存椂寮哄埗 `contract_failed`銆?  - 浜屾妫€鏌?evidence manifest锛屽彂鐜扮己澶辨椂寮哄埗 `contract_failed` 骞惰ˉ鍏?reason code銆?  - 鏀寔 `--github-output` 瀵煎嚭 verdict 鐘舵€併€佸喅绛栥€乺un_id/url 涓庢姤鍛婅矾寰勶紝渚?Linux CI 缁堢偣 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_verdict_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_verdict_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚release_archive_status=ready` + 濂戠害涓€鑷存椂蹇呴』鏀舵暃涓?`release_verdict_status=published` 涓?`release_verdict_decision=ship`銆?  - `T2`锛歚release_archive_status=pending` 鏃跺繀椤绘敹鏁涗负 `release_verdict_status=awaiting_archive` 涓斾繚鎸?hold 璇箟銆?  - `T3`锛歛rchive 濂戠害涓嶄竴鑷达紙濡?ready 浣?decision!=publish锛夋椂蹇呴』鏀舵暃涓?`release_verdict_status=contract_failed`銆?  - `T4`锛歟vidence 缂哄け鏃跺繀椤绘爣璁?missing artifacts 骞舵敹鏁涗负 `contract_failed`銆?  - `T5`锛欸itHub output 濂戠害蹇呴』鍖呭惈 verdict 鐘舵€併€佸喅绛栥€乺un_id/url銆乵issing artifacts 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-37`

## P2-39 Linux CI Workflow Release Incident Dispatch Gate
- 鍗″彿锛歚P2-39`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-38` 宸茶緭鍑?release verdict 涓?`should_open_incident` 璇箟锛屼絾 Linux CI 浠嶇己灏戠粺涓€鈥滀綍鏃?濡備綍瑙﹀彂 incident鈥濈殑鎵ц濂戠害锛屼笅娓搁渶瑕佽嚜琛屾嫾鎺ュ懡浠や笌澶辫触璇箟銆?  - 缂哄皯 incident dispatch 鍗曞嚭鍙ｆ椂锛岀粓鐐瑰憡璀﹂摼璺紙issue/incident system锛夊鏄撳嚭鐜拌Е鍙戞紡鎶ャ€侀噸澶嶈Е鍙戞垨澶辫触涓嶅彲瀹¤銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 release incident gate锛岃鍙?`P2-38` release verdict 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_incident.json`
    - `ci_workflow_release_incident.md`
  - 灏?verdict 璇箟缁熶竴鏀舵暃涓猴細
    - `incident_dispatch_status`锛坄not_required` / `ready_dry_run` / `dispatched` / `dispatch_failed` / `contract_failed`锛?    - `should_dispatch_incident`
    - `incident_dispatch_exit_code`
  - 鍥哄寲 verdict 濂戠害涓€鑷存€ф牎楠岋紙濡?`release_verdict_status=published` 蹇呴』 `should_open_incident=false`锛夛紝涓嶄竴鑷存椂寮哄埗 `contract_failed`銆?  - 鏀寔 auto incident command锛堥粯璁?`gh issue create`锛変笌 `--incident-command` 瑕嗙洊锛屽け璐ユ椂缁熶竴鏀舵暃 error reason銆?  - 鏀寔 `--github-output` 瀵煎嚭 incident 鐘舵€併€佹槸鍚﹁Е鍙戙€乮ncident url銆乺un_id/url 涓庢姤鍛婅矾寰勶紝渚?Linux CI 缁堢偣 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_incident_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_incident_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚release_verdict_status=published` + 濂戠害涓€鑷存椂蹇呴』鏀舵暃涓?`incident_dispatch_status=not_required`銆?  - `T2`锛歚release_verdict_status=blocked` 涓?`should_open_incident=true` 鏃讹紝dry-run 蹇呴』鏀舵暃涓?`incident_dispatch_status=ready_dry_run`銆?  - `T3`锛歷erdict 濂戠害涓嶄竴鑷达紙濡?published 浣?`should_open_incident=true`锛夋椂蹇呴』鏀舵暃涓?`incident_dispatch_status=contract_failed`銆?  - `T4`锛歩ncident command 澶辫触鏃跺繀椤绘敹鏁涗负 `incident_dispatch_status=dispatch_failed` 骞惰ˉ鍏?failure reason code銆?  - `T5`锛欸itHub output 濂戠害蹇呴』鍖呭惈 incident 鐘舵€併€佹槸鍚﹁Е鍙戙€乮ncident url銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-38`
## P2-40 Linux CI Workflow Release Terminal Verdict Publish Gate
- 鍗″彿锛歚P2-40`
- 浼樺厛绾э細`P2`
- 瑙ｅ喅闂锛?  - `P2-39` 宸茶緭鍑?incident dispatch 濂戠害锛屼絾 Linux CI 缁堢偣浠嶇己灏戠粺涓€鈥滄渶缁堝彂甯冨垽璇嶁€濇敹鍙ｏ紱涓嬫父浠嶉渶鑷鎷兼帴 ship/hold/escalate/block 璇箟銆?  - 缂哄皯 terminal verdict 鍗曞嚭鍙ｆ椂锛宺elease 缁堝眬鐪嬫澘涓庤嚜鍔ㄥ寲闂幆锛堥€氱煡銆佷汉宸ユ帴绠°€侀樆鏂級鏄撳嚭鐜拌涔夋紓绉讳笌閲嶅鍒ゅ畾銆?- 鐮斿彂鍔熻兘锛?  - 鏂板 release terminal verdict gate锛岃鍙?`P2-39` release incident 鎶ュ憡骞惰緭鍑猴細
    - `ci_workflow_release_terminal_verdict.json`
    - `ci_workflow_release_terminal_verdict.md`
  - 灏?release+incident 璇箟缁熶竴鏀舵暃涓猴細
    - `release_terminal_verdict_status`锛坄released` / `awaiting_archive` / `blocked_incident_ready_dry_run` / `blocked_incident_dispatched` / `blocked_incident_failed` / `blocked` / `contract_failed`锛?    - `release_terminal_verdict_decision`锛坄ship` / `hold` / `escalate` / `block`锛?    - `release_terminal_verdict_exit_code`
    - `terminal_should_ship_release`
    - `terminal_requires_follow_up`
  - 鍥哄寲 `P2-38` + `P2-39` 濂戠害涓€鑷存€ф牎楠岋紙渚嬪 `release_verdict_status=published` 蹇呴』 `should_open_incident=false` 涓?`incident_dispatch_status=not_required`锛夛紝涓嶄竴鑷村己鍒?`contract_failed`銆?  - 鏀寔 `--github-output` 瀵煎嚭 terminal verdict 鐘舵€併€佸喅绛栥€乪xit code銆乮ncident 鐘舵€?url銆乺un_id/url 涓庢姤鍛婅矾寰勶紝渚?Linux CI 缁堢偣 job 鐩存帴娑堣垂銆?- 瀹炴柦鑼冨洿锛?  - `scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_terminal_verdict_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- 娴嬭瘯浠ｇ爜瑕佹眰锛?  - `T1`锛歚release_verdict_status=published` + `incident_dispatch_status=not_required` 鏃跺繀椤绘敹鏁涗负 `release_terminal_verdict_status=released`銆?  - `T2`锛歚release_verdict_status=blocked` + `incident_dispatch_status=ready_dry_run` 鏃讹紝蹇呴』鏀舵暃涓?`release_terminal_verdict_status=blocked_incident_ready_dry_run` 涓?decision=`escalate`銆?  - `T3`锛氬绾︿笉涓€鑷达紙濡?published 浣?`should_open_incident=true`锛夋椂蹇呴』鏀舵暃涓?`release_terminal_verdict_status=contract_failed`銆?  - `T4`锛氳瘉鎹己澶辨椂蹇呴』鏀舵暃涓?`release_terminal_verdict_status=contract_failed` 骞惰ˉ鍏?missing artifact reason銆?  - `T5`锛欸itHub output 濂戠害蹇呴』鍖呭惈 terminal verdict 鐘舵€併€佸喅绛栥€乪xit code銆乮ncident 鐘舵€?url銆乺un_id/url 涓庢姤鍛婅矾寰勩€?- 鍓嶇疆渚濊禆锛歚P2-39`

## P2-41 Linux CI Workflow Release Delivery Closure Gate
- ???`P2-41`
- ????`P2`
- ?????
  - `P2-40` ??? terminal verdict ???? Linux CI ??????????????????????????????????
  - ?? delivery closure gate ??????? ship/hold/escalate/block ????????????????????????????
- ?????
  - ?? release delivery gate??? `P2-40` release terminal verdict ??????
    - `ci_workflow_release_delivery.json`
    - `ci_workflow_release_delivery.md`
  - ? terminal verdict + incident ????????
    - `release_delivery_status`?`shipped` / `pending_follow_up` / `blocked_incident` / `blocked_incident_failed` / `blocked` / `contract_failed`?
    - `release_delivery_decision`?`deliver` / `hold` / `escalate` / `block`?
    - `release_delivery_exit_code`
    - `delivery_should_ship_release`
    - `delivery_requires_human_action`
    - `delivery_should_announce_blocker`
  - ?? `P2-40` ?????????? `release_terminal_verdict_status=released` ?? `incident_dispatch_status=not_required`??????? `contract_failed`?
  - ?? `--github-output` ?? delivery ??????exit code??????????incident ??/url?run_id/url ??????
- ?????
  - `scripts/run_p2_linux_ci_workflow_release_delivery_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_delivery_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- ???????
  - `T1`?`release_terminal_verdict_status=released` + `incident_dispatch_status=not_required` ?????? `release_delivery_status=shipped` ? decision=`deliver`?
  - `T2`?`release_terminal_verdict_status=blocked_incident_ready_dry_run` ?????? `release_delivery_status=blocked_incident` ? decision=`escalate`?
  - `T3`???????? `released` ? `incident_dispatch_status=ready_dry_run`??????? `release_delivery_status=contract_failed`?
  - `T4`??????????? `release_delivery_status=contract_failed` ??? missing artifact reason?
  - `T5`?GitHub output ?????? delivery ??????exit code????????incident ??/url?run_id/url ??????
- ?????`P2-40`


## P2-42 Linux CI Workflow Release Delivery Terminal Publish Gate
- Card ID: `P2-42`
- Priority: `P2`
- Problem:
  - `P2-41` converges to delivery semantics, but Linux CI still lacks one terminal publish contract for downstream notification/hand-off consumers.
  - Without one terminal publish output, follow-up automation and human takeover paths must re-interpret delivery fields independently.
- Scope:
  - Add terminal publish gate that consumes `P2-41` delivery report and emits:
    - `ci_workflow_release_delivery_terminal_publish.json`
    - `ci_workflow_release_delivery_terminal_publish.md`
  - Converge to normalized outputs:
    - `release_delivery_terminal_publish_status` (`published`/`pending_follow_up`/`blocked`/`contract_failed`)
    - `release_delivery_terminal_publish_decision` (`announce_release`/`announce_hold`/`announce_blocker`/`abort_publish`)
    - `release_delivery_terminal_publish_exit_code`
    - `terminal_publish_should_notify` / `terminal_publish_should_create_follow_up` / `terminal_publish_channel`
  - Export `--github-output` fields for Linux CI terminal job consumption.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_delivery_terminal_publish_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: `release_delivery_status=shipped` converges to `published` + `announce_release`.
  - `T2`: `release_delivery_status=blocked_incident` converges to `blocked` + `announce_blocker`.
  - `T3`: delivery/incident contract mismatch converges to `contract_failed`.
  - `T4`: missing evidence converges to `contract_failed` with missing-artifact reason.
  - `T5`: GitHub output includes status/decision/exit_code/channel/run_id/run_url.
- Depends on: `P2-41`

## P2-43 Linux CI Workflow Release Delivery Final Verdict Gate
- Card ID: `P2-43`
- Priority: `P2`
- Problem:
  - `P2-42` converges release delivery to terminal publish semantics, but Linux CI still lacks one final closure verdict contract for release close/follow-up/escalation takeover.
  - Without one final verdict output, downstream consumers must re-interpret terminal publish + delivery + incident fields independently.
- Scope:
  - Add final verdict gate that consumes `P2-42` delivery terminal publish report and emits:
    - `ci_workflow_release_delivery_final_verdict.json`
    - `ci_workflow_release_delivery_final_verdict.md`
  - Converge to normalized outputs:
    - `release_delivery_final_verdict_status` (`completed`/`requires_follow_up`/`blocked`/`contract_failed`)
    - `release_delivery_final_verdict_decision` (`close_release`/`open_follow_up`/`escalate_blocker`/`abort_close`)
    - `release_delivery_final_verdict_exit_code`
    - `final_should_close_release` / `final_should_open_follow_up` / `final_should_page_owner` / `final_announcement_target`
  - Export `--github-output` fields for Linux CI terminal closeout job consumption.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_delivery_final_verdict_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: `release_delivery_terminal_publish_status=published` converges to `completed` + `close_release`.
  - `T2`: `release_delivery_terminal_publish_status=pending_follow_up` converges to `requires_follow_up` + `open_follow_up`.
  - `T3`: terminal publish / delivery / incident contract mismatch converges to `contract_failed`.
  - `T4`: missing evidence converges to `contract_failed` with missing-artifact reason.
  - `T5`: GitHub output includes status/decision/exit_code/final-action booleans/announcement_target/run_id/run_url.
- Depends on: `P2-42`

## P2-44 Linux CI Workflow Release Follow-Up Dispatch Gate
- Card ID: `P2-44`
- Priority: `P2`
- Problem:
  - `P2-43` converges release delivery to final verdict semantics, but Linux CI still lacks one terminal follow-up dispatch contract for queue/escalation takeover consumers.
  - Without one follow-up dispatch output, downstream automation must re-interpret final verdict + incident + publish fields independently.
- Scope:
  - Add follow-up dispatch gate that consumes `P2-43` delivery final verdict report and emits:
    - `ci_workflow_release_follow_up_dispatch.json`
    - `ci_workflow_release_follow_up_dispatch.md`
  - Converge to normalized outputs:
    - `release_follow_up_dispatch_status` (`closed`/`follow_up_required`/`escalated`/`contract_failed`)
    - `release_follow_up_dispatch_decision` (`no_action`/`dispatch_follow_up`/`dispatch_escalation`/`abort_dispatch`)
    - `release_follow_up_dispatch_exit_code`
    - `follow_up_required` / `escalation_required` / `dispatch_target`
  - Export `--github-output` fields for Linux CI final hand-off consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_follow_up_dispatch_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: `release_delivery_final_verdict_status=completed` converges to `closed` + `no_action`.
  - `T2`: `release_delivery_final_verdict_status=requires_follow_up` converges to `follow_up_required` + `dispatch_follow_up`.
  - `T3`: final-verdict contract mismatch converges to `contract_failed`.
  - `T4`: missing evidence converges to `contract_failed` with missing-artifact reason.
  - `T5`: GitHub output includes status/decision/exit_code/follow-up/escalation booleans/dispatch_target/run_id/run_url.
- Depends on: `P2-43`

## P2-45 Linux CI Workflow Release Follow-Up Closure Gate
- Card ID: `P2-45`
- Priority: `P2`
- Problem:
  - `P2-44` converges release delivery final verdict to follow-up dispatch semantics, but Linux CI still lacks one terminal follow-up closure contract for backlog ownership/queue intake consumers.
  - Without one follow-up closure output, downstream automation must re-interpret dispatch status + target + escalation flags and cannot safely distinguish dry-run readiness vs actual queue success.
- Scope:
  - Add follow-up closure gate that consumes `P2-44` release follow-up dispatch report and emits:
    - `ci_workflow_release_follow_up_closure.json`
    - `ci_workflow_release_follow_up_closure.md`
  - Converge to normalized outputs:
    - `release_follow_up_closure_status` (`closed`/`queued_dry_run`/`queued`/`queue_failed`/`contract_failed`)
    - `release_follow_up_closure_decision` (`no_action`/`queue_follow_up`/`queue_escalation`/`abort_queue`)
    - `release_follow_up_closure_exit_code`
    - `should_queue_follow_up` / `follow_up_queue_attempted` / `follow_up_task_queued` / `escalation_task_queued`
  - Export `--github-output` fields for Linux CI terminal follow-up hand-off consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_follow_up_closure_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: `release_follow_up_dispatch_status=closed` converges to `closed` + `no_action`.
  - `T2`: `release_follow_up_dispatch_status=follow_up_required` converges to `queued_dry_run` + `queue_follow_up` in dry-run mode.
  - `T3`: follow-up dispatch contract mismatch converges to `contract_failed`.
  - `T4`: executable follow-up queue command failure converges to `queue_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/queue booleans/target/queue_url/run_id/run_url.
- Depends on: `P2-44`

## P2-46 Linux CI Workflow Release Follow-Up Terminal Publish Gate
- Card ID: `P2-46`
- Priority: `P2`
- Problem:
  - `P2-45` converges follow-up dispatch to closure semantics, but Linux CI still lacks one terminal publish contract that cleanly separates `closed`/`queued`/`pending_queue`/`queue_failed` outcomes for downstream notification and hand-off jobs.
  - Without one terminal publish output, downstream automation must re-interpret closure status + queue attempt fields and cannot consume a single stable final follow-up signal.
- Scope:
  - Add follow-up terminal publish gate that consumes `P2-45` release follow-up closure report and emits:
    - `ci_workflow_release_follow_up_terminal_publish.json`
    - `ci_workflow_release_follow_up_terminal_publish.md`
  - Converge to normalized outputs:
    - `release_follow_up_terminal_publish_status` (`published`/`pending_queue`/`queue_failed`/`contract_failed`)
    - `release_follow_up_terminal_publish_decision` (`announce_closed`/`announce_queued`/`announce_pending_queue`/`announce_queue_failure`/`abort_publish`)
    - `release_follow_up_terminal_publish_exit_code`
    - `follow_up_terminal_publish_should_notify` / `follow_up_terminal_requires_manual_action` / `follow_up_terminal_publish_channel`
  - Export `--github-output` fields for Linux CI terminal follow-up publish consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: `release_follow_up_closure_status=closed` converges to `published` + `announce_closed`.
  - `T2`: `release_follow_up_closure_status=queued_dry_run` converges to `pending_queue` + `announce_pending_queue`.
  - `T3`: closure contract mismatch converges to `contract_failed`.
  - `T4`: `release_follow_up_closure_status=queue_failed` converges to `queue_failed` + `announce_queue_failure`.
  - `T5`: GitHub output includes status/decision/exit_code/notify/manual-action/channel/closure-status/queue-url/run_id/run_url.
- Depends on: `P2-45`

## P2-47 Linux CI Workflow Release Follow-Up Final Verdict Gate
- Card ID: `P2-47`
- Priority: `P2`
- Problem:
  - `P2-46` converges follow-up closure to terminal publish semantics, but Linux CI still lacks one final verdict contract that cleanly separates `completed`/`requires_follow_up`/`blocked`/`contract_failed` outcomes for post-release ownership and escalation consumers.
  - Without one final verdict output, downstream automation must re-interpret terminal publish + closure + queue fields and cannot consume one stable close/open/escalate signal.
- Scope:
  - Add follow-up final verdict gate that consumes `P2-46` release follow-up terminal publish report and emits:
    - `ci_workflow_release_follow_up_final_verdict.json`
    - `ci_workflow_release_follow_up_final_verdict.md`
  - Converge to normalized outputs:
    - `release_follow_up_final_verdict_status` (`completed`/`requires_follow_up`/`blocked`/`contract_failed`)
    - `release_follow_up_final_verdict_decision` (`close_follow_up`/`keep_follow_up_open`/`escalate_queue_failure`/`abort_close`)
    - `release_follow_up_final_verdict_exit_code`
    - `final_should_close_follow_up` / `final_should_open_follow_up` / `final_should_page_owner` / `final_announcement_target`
  - Export `--github-output` fields for Linux CI terminal follow-up ownership consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_follow_up_final_verdict_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: `release_follow_up_terminal_publish_status=published` + `announce_closed` converges to `completed` + `close_follow_up`.
  - `T2`: `release_follow_up_terminal_publish_status=pending_queue` converges to `requires_follow_up` + `keep_follow_up_open`.
  - `T3`: `release_follow_up_terminal_publish_status=queue_failed` converges to `blocked` + `escalate_queue_failure`.
  - `T4`: terminal publish / closure contract mismatch converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/final booleans/announcement-target/terminal-channel/queue-url/run_id/run_url.
- Depends on: `P2-46`

## P2-48 Linux CI Workflow Release Final Outcome Gate
- Card ID: `P2-48`
- Priority: `P2`
- Problem:
  - `P2-43` delivers release final verdict semantics and `P2-47` delivers follow-up final verdict semantics, but Linux CI still lacks one single terminal outcome contract that downstream release governance and notification consumers can consume without re-stitching two reports.
  - Without one final outcome output, downstream automation must merge delivery/follow-up statuses itself and risks drift on ship-with-follow-up vs blocked escalation semantics.
- Scope:
  - Add release final outcome gate that consumes `P2-43` release delivery final verdict report and `P2-47` release follow-up final verdict report and emits:
    - `ci_workflow_release_final_outcome.json`
    - `ci_workflow_release_final_outcome.md`
  - Converge to normalized outputs:
    - `release_final_outcome_status` (`released`/`released_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_outcome_decision` (`ship_and_close`/`ship_with_follow_up_open`/`escalate_blocker`/`abort_outcome`)
    - `release_final_outcome_exit_code`
    - `final_should_ship_release` / `final_follow_up_open` / `final_should_page_owner` / `final_outcome_target`
  - Export `--github-output` fields for Linux CI terminal release ownership consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_outcome_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: delivery=`completed` + follow-up=`completed` converges to `released` + `ship_and_close`.
  - `T2`: delivery=`completed` + follow-up=`requires_follow_up` converges to `released_with_follow_up` + `ship_with_follow_up_open`.
  - `T3`: delivery or follow-up=`blocked` converges to `blocked` + `escalate_blocker`.
  - `T4`: delivery/follow-up contract mismatch (decision/flags/run-id) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/ship+follow-up flags/target/queue-url/run-id/run-url/report paths.
- Depends on: `P2-43`, `P2-47`

## P2-49 Linux CI Workflow Release Final Terminal Publish Gate
- Card ID: `P2-49`
- Priority: `P2`
- Problem:
  - `P2-48` already converges one final release outcome artifact, but Linux CI still lacks one terminal publish contract dedicated to final stakeholder-facing announcement semantics.
  - Without a dedicated terminal publish gate, downstream consumers still need custom mapping from outcome states to channel/action semantics, increasing drift risk on `released_with_follow_up` vs `blocked` paths.
- Scope:
  - Add release final terminal publish gate that consumes `P2-48` release final outcome report and emits:
    - `ci_workflow_release_final_terminal_publish.json`
    - `ci_workflow_release_final_terminal_publish.md`
  - Converge to normalized outputs:
    - `release_final_terminal_publish_status` (`published`/`published_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_terminal_publish_decision` (`announce_release_closure`/`announce_release_with_follow_up`/`announce_blocker`/`abort_publish`)
    - `release_final_terminal_publish_exit_code`
    - `final_terminal_should_notify` / `final_terminal_requires_manual_action` / `final_terminal_channel`
  - Export `--github-output` fields for Linux CI terminal publish/notification consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_terminal_publish_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: final outcome=`released` converges to `published` + `announce_release_closure`.
  - `T2`: final outcome=`released_with_follow_up` converges to `published_with_follow_up` + `announce_release_with_follow_up`.
  - `T3`: final outcome=`blocked` converges to `blocked` + `announce_blocker`.
  - `T4`: final outcome contract mismatch (decision/flags/target) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/notify+manual-action/channel/run-id/run-url/report paths.
- Depends on: `P2-48`

## P2-50 Linux CI Workflow Release Final Handoff Gate
- Card ID: `P2-50`
- Priority: `P2`
- Problem:
  - `P2-49` already converges final terminal publish semantics, but Linux CI still lacks one terminal handoff contract that downstream closure/archive consumers can consume directly without remapping publish statuses.
  - Without this dedicated handoff gate, downstream automation still repeats custom logic for `published_with_follow_up` versus `blocked` paths, increasing drift risk on archive/handoff ownership semantics.
- Scope:
  - Add release final handoff gate that consumes `P2-49` release final terminal publish report and emits:
    - `ci_workflow_release_final_handoff.json`
    - `ci_workflow_release_final_handoff.md`
  - Converge to normalized outputs:
    - `release_final_handoff_status` (`completed`/`completed_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_handoff_decision` (`handoff_release_closure`/`handoff_release_with_follow_up`/`handoff_blocker`/`abort_handoff`)
    - `release_final_handoff_exit_code`
    - `final_handoff_should_archive_release` / `final_handoff_keep_follow_up_open` / `final_handoff_should_page_owner` / `final_handoff_target`
  - Export `--github-output` fields for Linux CI terminal handoff/closure consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_handoff_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: final terminal publish=`published` converges to `completed` + `handoff_release_closure`.
  - `T2`: final terminal publish=`published_with_follow_up` converges to `completed_with_follow_up` + `handoff_release_with_follow_up`.
  - `T3`: final terminal publish=`blocked` converges to `blocked` + `handoff_blocker`.
  - `T4`: final terminal publish contract mismatch (decision/flags/channel/target) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/archive+follow-up+page flags/target/queue-url/run-id/run-url/report paths.
- Depends on: `P2-49`

## P2-51 Linux CI Workflow Release Final Closure Gate
- Card ID: `P2-51`
- Priority: `P2`
- Problem:
  - `P2-50` already converges final handoff semantics, but Linux CI still lacks one terminal closure contract that downstream owner-closure consumers can consume directly without remapping handoff statuses.
  - Without this dedicated closure gate, downstream automation still repeats custom logic for `completed_with_follow_up` versus `blocked` paths, increasing drift risk on final close ownership semantics.
- Scope:
  - Add release final closure gate that consumes `P2-50` release final handoff report and emits:
    - `ci_workflow_release_final_closure.json`
    - `ci_workflow_release_final_closure.md`
  - Converge to normalized outputs:
    - `release_final_closure_status` (`closed`/`closed_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_closure_decision` (`close_release`/`close_with_follow_up`/`close_blocker`/`abort_close`)
    - `release_final_closure_exit_code`
    - `final_closure_is_closed` / `final_closure_has_open_follow_up` / `final_closure_should_page_owner` / `final_closure_target`
  - Export `--github-output` fields for Linux CI terminal closure consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_closure_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: final handoff=`completed` converges to `closed` + `close_release`.
  - `T2`: final handoff=`completed_with_follow_up` converges to `closed_with_follow_up` + `close_with_follow_up`.
  - `T3`: final handoff=`blocked` converges to `blocked` + `close_blocker`.
  - `T4`: final handoff contract mismatch (decision/flags/target) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/closed+follow-up+page flags/target/queue-url/run-id/run-url/report paths.
- Depends on: `P2-50`

## P2-52 Linux CI Workflow Release Final Closure Publish Gate
- Card ID: `P2-52`
- Priority: `P2`
- Problem:
  - `P2-51` already converges final closure semantics, but Linux CI still lacks one terminal publish contract dedicated to final closure announcement semantics for downstream consumers.
  - Without this dedicated closure-publish gate, downstream automation still repeats custom logic for `closed_with_follow_up` versus `blocked` paths, increasing drift risk on final announce/manual-action semantics.
- Scope:
  - Add release final closure publish gate that consumes `P2-51` release final closure report and emits:
    - `ci_workflow_release_final_closure_publish.json`
    - `ci_workflow_release_final_closure_publish.md`
  - Converge to normalized outputs:
    - `release_final_closure_publish_status` (`published`/`published_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_closure_publish_decision` (`announce_release_closed`/`announce_release_closed_with_follow_up`/`announce_release_blocker`/`abort_publish`)
    - `release_final_closure_publish_exit_code`
    - `final_closure_publish_should_notify` / `final_closure_publish_requires_manual_action` / `final_closure_publish_channel`
  - Export `--github-output` fields for Linux CI final closure publish consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_closure_publish_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: final closure=`closed` converges to `published` + `announce_release_closed`.
  - `T2`: final closure=`closed_with_follow_up` converges to `published_with_follow_up` + `announce_release_closed_with_follow_up`.
  - `T3`: final closure=`blocked` converges to `blocked` + `announce_release_blocker`.
  - `T4`: final closure contract mismatch (decision/flags/target) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/notify+manual-action/channel/queue-url/run-id/run-url/report paths.
- Depends on: `P2-51`

## P2-53 Linux CI Workflow Release Final Archive Gate
- Card ID: `P2-53`
- Priority: `P2`
- Problem:
  - `P2-52` already converges terminal closure publish semantics, but Linux CI still lacks one terminal archive contract that downstream archival/compliance consumers can consume directly without remapping publish statuses.
  - Without this dedicated final-archive gate, downstream automation still repeats custom logic for `published_with_follow_up` versus `blocked` paths, increasing drift risk on archive/manual-action semantics.
- Scope:
  - Add release final archive gate that consumes `P2-52` release final closure publish report and emits:
    - `ci_workflow_release_final_archive.json`
    - `ci_workflow_release_final_archive.md`
  - Converge to normalized outputs:
    - `release_final_archive_status` (`archived`/`archived_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_archive_decision` (`archive_release_closed`/`archive_release_closed_with_follow_up`/`archive_release_blocker`/`abort_archive`)
    - `release_final_archive_exit_code`
    - `final_archive_should_publish` / `final_archive_requires_manual_action` / `final_archive_channel`
  - Export `--github-output` fields for Linux CI final archive consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_archive_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: final closure publish=`published` converges to `archived` + `archive_release_closed`.
  - `T2`: final closure publish=`published_with_follow_up` converges to `archived_with_follow_up` + `archive_release_closed_with_follow_up`.
  - `T3`: final closure publish=`blocked` converges to `blocked` + `archive_release_blocker`.
  - `T4`: final closure publish contract mismatch (decision/flags/channel) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/publish+manual-action/channel/queue-url/run-id/run-url/report paths.
- Depends on: `P2-52`

## P2-54 Linux CI Workflow Release Final Verdict Gate
- Card ID: `P2-54`
- Priority: `P2`
- Problem:
  - `P2-53` already converges final archive semantics, but Linux CI still lacks one terminal final-verdict contract that downstream release decision consumers can consume directly without remapping archive statuses.
  - Without this dedicated final-verdict gate, downstream automation still repeats custom logic for `archived_with_follow_up` versus `blocked` paths, increasing drift risk on ship/manual-action semantics.
- Scope:
  - Add release final verdict gate that consumes `P2-53` release final archive report and emits:
    - `ci_workflow_release_final_verdict.json`
    - `ci_workflow_release_final_verdict.md`
  - Converge to normalized outputs:
    - `release_final_verdict_status` (`released`/`released_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_verdict_decision` (`ship_release`/`ship_release_with_follow_up`/`escalate_release_blocker`/`abort_verdict`)
    - `release_final_verdict_exit_code`
    - `final_verdict_should_ship` / `final_verdict_requires_manual_action` / `final_verdict_channel`
  - Export `--github-output` fields for Linux CI final verdict consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_verdict_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: final archive=`archived` converges to `released` + `ship_release`.
  - `T2`: final archive=`archived_with_follow_up` converges to `released_with_follow_up` + `ship_release_with_follow_up`.
  - `T3`: final archive=`blocked` converges to `blocked` + `escalate_release_blocker`.
  - `T4`: final archive contract mismatch (decision/flags/channel) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/ship+manual-action/channel/queue-url/run-id/run-url/report paths.
- Depends on: `P2-53`

## P2-55 Linux CI Workflow Release Final Verdict Publish Gate
- Card ID: `P2-55`
- Priority: `P2`
- Problem:
  - `P2-54` already converges final verdict semantics, but Linux CI still lacks one terminal publish contract that downstream notification/audit consumers can consume directly without remapping verdict statuses.
  - Without this dedicated final-verdict-publish gate, downstream automation still repeats custom logic for `released_with_follow_up` versus `blocked` paths, increasing drift risk on notify/manual-action semantics.
- Scope:
  - Add release final verdict publish gate that consumes `P2-54` release final verdict report and emits:
    - `ci_workflow_release_final_verdict_publish.json`
    - `ci_workflow_release_final_verdict_publish.md`
  - Converge to normalized outputs:
    - `release_final_verdict_publish_status` (`published`/`published_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_verdict_publish_decision` (`announce_release_shipped`/`announce_release_shipped_with_follow_up`/`announce_release_blocker`/`abort_publish`)
    - `release_final_verdict_publish_exit_code`
    - `final_verdict_publish_should_notify` / `final_verdict_publish_requires_manual_action` / `final_verdict_publish_channel`
  - Export `--github-output` fields for Linux CI final verdict publish consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_verdict_publish_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: final verdict=`released` converges to `published` + `announce_release_shipped`.
  - `T2`: final verdict=`released_with_follow_up` converges to `published_with_follow_up` + `announce_release_shipped_with_follow_up`.
  - `T3`: final verdict=`blocked` converges to `blocked` + `announce_release_blocker`.
  - `T4`: final verdict contract mismatch (decision/flags/channel) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/notify+manual-action/channel/queue-url/run-id/run-url/report paths.
- Depends on: `P2-54`

## P2-56 Linux CI Workflow Release Final Publish Archive Gate
- Card ID: `P2-56`
- Priority: `P2`
- Problem:
  - `P2-55` already converges final verdict publish semantics, but Linux CI still lacks one terminal archive contract that downstream archival/compliance consumers can consume directly without remapping publish statuses.
  - Without this dedicated final-publish-archive gate, downstream automation still repeats custom logic for `published_with_follow_up` versus `blocked` paths, increasing drift risk on archive/manual-action semantics.
- Scope:
  - Add release final publish archive gate that consumes `P2-55` release final verdict publish report and emits:
    - `ci_workflow_release_final_publish_archive.json`
    - `ci_workflow_release_final_publish_archive.md`
  - Converge to normalized outputs:
    - `release_final_publish_archive_status` (`archived`/`archived_with_follow_up`/`blocked`/`contract_failed`)
    - `release_final_publish_archive_decision` (`archive_release_shipped`/`archive_release_shipped_with_follow_up`/`archive_release_blocker`/`abort_archive`)
    - `release_final_publish_archive_exit_code`
    - `final_publish_archive_should_archive` / `final_publish_archive_requires_manual_action` / `final_publish_archive_channel`
  - Export `--github-output` fields for Linux CI final publish archive consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py`
  - `tests/test_p2_linux_ci_workflow_release_final_publish_archive_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: final verdict publish=`published` converges to `archived` + `archive_release_shipped`.
  - `T2`: final verdict publish=`published_with_follow_up` converges to `archived_with_follow_up` + `archive_release_shipped_with_follow_up`.
  - `T3`: final verdict publish=`blocked` converges to `blocked` + `archive_release_blocker`.
  - `T4`: final verdict publish contract mismatch (decision/flags/channel) converges to `contract_failed`.
  - `T5`: GitHub output includes status/decision/exit_code/archive+manual-action/channel/queue-url/run-id/run-url/report paths.
- Depends on: `P2-55`

## P2-57 Linux Gate Manifest Drift Closure Gate
- Card ID: `P2-57`
- Priority: `P2`
- Problem:
  - As `P2-xx` gate cards keep growing, there is no single guard that continuously verifies closure across gate scripts, runtime contract tests, and Linux unified manifest wiring.
  - Without this closure gate, future card additions can silently miss `test_*_gate_runtime.py` or omit Linux manifest entries, only failing late in Linux stage.
- Scope:
  - Add a dedicated drift-closure gate that scans:
    - `scripts/run_*_gate.py` (excluding `run_linux_unified_gate.py`)
    - expected `tests/test_*_gate_runtime.py`
    - `scripts/run_linux_unified_gate.py::LINUX_UNIFIED_TEST_FILES`
  - Emit normalized drift report artifacts:
    - `.claude/reports/linux_unified_gate/linux_gate_manifest_drift.json`
    - `.claude/reports/linux_unified_gate/linux_gate_manifest_drift.md`
  - Export `--github-output` fields for CI observability:
    - status + missing-runtime-tests count + missing-manifest count + orphan-manifest count.
- Implementation:
  - `scripts/run_p2_linux_gate_manifest_drift_gate.py`
  - `tests/test_p2_linux_gate_manifest_drift_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: gate script scan includes `run_p2_linux_gate_manifest_drift_gate.py` and excludes `run_linux_unified_gate.py`.
  - `T2`: expected runtime test mapping follows `run_xxx_gate.py` -> `test_xxx_gate_runtime.py`.
  - `T3`: repository baseline report converges to `status=passed` with zero missing runtime tests / manifest entries / orphan manifest entries.
  - `T4`: GitHub output fields expose status and drift counters.
- Depends on: `P2-56`

## P2-59 Linux CI Workflow Terminal Verdict Closure Gate
- Card ID: `P2-59`
- Priority: `P2`
- Problem:
  - `P2-56` and `P2-57` are both terminal quality signals, but Linux CI still lacks one single contract that downstream automation can consume as a final go/no-go verdict.
  - Without a unified terminal verdict, Linux validation entry and release control logic must duplicate merge rules across two artifacts, increasing drift risk.
- Scope:
  - Add one terminal verdict gate that consumes:
    - `.claude/reports/linux_unified_gate/ci_workflow_release_final_publish_archive.json` (`P2-56`)
    - `.claude/reports/linux_unified_gate/linux_gate_manifest_drift.json` (`P2-57`)
  - Emit normalized outputs:
    - `terminal_verdict_status` (`ready_for_linux_validation`/`ready_with_follow_up_for_linux_validation`/`blocked`/`contract_failed`)
    - `terminal_verdict_decision` (`proceed_linux_validation`/`proceed_linux_validation_with_follow_up`/`halt_linux_validation_blocker`/`abort_linux_validation`)
    - `terminal_verdict_exit_code`
    - `terminal_verdict_should_proceed` / `terminal_verdict_requires_manual_action` / `terminal_verdict_channel`
  - Export `--github-output` fields for Linux CI consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py`
  - `tests/test_p2_linux_ci_workflow_terminal_verdict_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: publish-archive=`archived` + drift=`passed` converges to `ready_for_linux_validation` + `proceed_linux_validation`.
  - `T2`: publish-archive=`archived_with_follow_up` + drift=`passed` converges to `ready_with_follow_up_for_linux_validation` + `proceed_linux_validation_with_follow_up`.
  - `T3`: publish-archive=`blocked` + drift=`passed` converges to `blocked` + `halt_linux_validation_blocker`.
  - `T4`: publish-archive mismatch or drift failure converges to `contract_failed` + `abort_linux_validation`.
  - `T5`: GitHub output includes status/decision/exit_code/proceed+manual-action/channel/drift counters/report paths.
- Depends on: `P2-57`

## P2-60 Linux CI Workflow Linux Validation Dispatch Gate
- Card ID: `P2-60`
- Priority: `P2`
- Problem:
  - `P2-59` gives a terminal go/no-go contract, but Linux CI still lacks a single dispatch contract that transforms terminal verdict into an executable Linux validation action.
  - Without a dedicated Linux-validation-dispatch gate, downstream jobs still duplicate mapping logic across `ready_for_linux_validation` / `ready_with_follow_up_for_linux_validation` / `blocked` / `contract_failed` paths.
- Scope:
  - Add one Linux validation dispatch gate that consumes:
    - `.claude/reports/linux_unified_gate/ci_workflow_terminal_verdict.json` (`P2-59`)
  - Emit normalized outputs:
    - `linux_validation_dispatch_status` (`ready_dry_run`/`ready_with_follow_up_dry_run`/`dispatched`/`dispatch_failed`/`blocked`/`contract_failed`)
    - `linux_validation_dispatch_decision` (`dispatch_linux_validation`/`dispatch_linux_validation_with_follow_up`/`hold_linux_validation_blocker`/`abort_linux_validation_dispatch`)
    - `linux_validation_dispatch_exit_code`
    - `linux_validation_should_dispatch` / `linux_validation_requires_manual_action` / `linux_validation_channel`
  - Support optional command execution with timeout control:
    - default command: `python scripts/run_p2_linux_unified_pipeline_gate.py --continue-on-failure`
    - optional override: `--linux-validation-command`
  - Export `--github-output` fields for CI consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_linux_validation_dispatch_gate.py`
  - `tests/test_p2_linux_ci_workflow_linux_validation_dispatch_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: terminal verdict=`ready_for_linux_validation` converges to `ready_dry_run` + `dispatch_linux_validation`.
  - `T2`: terminal verdict=`ready_with_follow_up_for_linux_validation` converges to `ready_with_follow_up_dry_run` + `dispatch_linux_validation_with_follow_up`.
  - `T3`: terminal verdict=`blocked` converges to `blocked` + `hold_linux_validation_blocker`.
  - `T4`: terminal verdict mismatch or drift/evidence issue converges to `contract_failed` + `abort_linux_validation_dispatch`.
  - `T5`: GitHub output includes status/decision/exit_code/dispatch+manual-action/channel/run-id/run-url/follow-up/report paths.
- Depends on: `P2-59`

## P2-61 Linux CI Workflow Linux Validation Verdict Gate
- Card ID: `P2-61`
- Priority: `P2`
- Problem:
  - `P2-60` converges Linux validation dispatch behavior, but Linux CI still lacks one terminal verdict artifact that downstream release governance can consume without re-parsing dispatch internals.
  - Without a dedicated Linux-validation-verdict gate, status handling for `dispatched/dispatch_failed/blocked/contract_failed` remains duplicated across consumers and can drift from terminal-verdict and manifest-drift contracts.
- Scope:
  - Add one Linux validation verdict gate that consumes:
    - `.claude/reports/linux_unified_gate/ci_workflow_linux_validation_dispatch.json` (`P2-60`)
  - Emit normalized outputs:
    - `linux_validation_verdict_status` (`validated`/`validated_with_follow_up`/`validation_failed`/`blocked`/`contract_failed`)
    - `linux_validation_verdict_decision` (`accept_linux_validation`/`accept_linux_validation_with_follow_up`/`escalate_linux_validation_failure`/`hold_linux_validation_blocker`/`abort_linux_validation_verdict`)
    - `linux_validation_verdict_exit_code`
    - `linux_validation_passed` / `linux_validation_verdict_requires_manual_action` / `linux_validation_verdict_channel`
  - Support optional verdict command execution with timeout control:
    - optional override: `--linux-validation-verdict-command`
    - timeout control: `--linux-validation-verdict-timeout-seconds`
  - Export `--github-output` fields for CI consumers.
- Implementation:
  - `scripts/run_p2_linux_ci_workflow_linux_validation_verdict_gate.py`
  - `tests/test_p2_linux_ci_workflow_linux_validation_verdict_gate_runtime.py`
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py`
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py`
  - `scripts/run_linux_unified_gate.py`
  - `README.md`
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md`
- Test Contract:
  - `T1`: dispatch=`dispatched` + terminal=`ready_for_linux_validation` converges to `validated` + `accept_linux_validation`.
  - `T2`: dispatch=`dispatched` + terminal=`ready_with_follow_up_for_linux_validation` converges to `validated_with_follow_up` + `accept_linux_validation_with_follow_up`.
  - `T3`: dispatch=`blocked` converges to `blocked` + `hold_linux_validation_blocker`.
  - `T4`: dispatch=`dispatch_failed` converges to `validation_failed` + `escalate_linux_validation_failure`; any contract mismatch/drift/evidence issue converges to `contract_failed` + `abort_linux_validation_verdict`.
  - `T5`: GitHub output includes verdict status/decision/exit_code/passed+manual-action/channel/dispatch status+decision/report paths.
- Depends on: `P2-60`

## 8. 鎺ㄨ崘杩唬椤哄簭

鑻ュ彧鍏佽涓€杞竴杞帹杩涳紝寤鸿椤哄簭濡備笅锛?
1. `P0-01`
2. `P0-02`
3. `P0-03`
4. `P0-04`
5. `P0-05`
6. `P0-06`
7. `P0-07`
8. `P0-09`
9. `P0-08`
10. `P0-10`

璇存槑锛?
- `P0-08` 涓嶉樆濉炰富鍔熻兘淇锛屽洜姝ゆ斁鍦?`P0-09` 鍚庨潰浜﹀彲
- `P0-10` 浣滀负鏀跺彛鍗★紝搴旀斁鍦?Phase 0 灏鹃儴

## 9. 姣忚疆杩唬鐨勬渶灏忎骇鍑鸿姹?
姣忓畬鎴愪竴寮犲崱锛岃嚦灏戝悓姝ヤ互涓嬩骇鐗╋細

1. 浠ｇ爜鍙樻洿
2. 娴嬭瘯鍙樻洿
3. 鏂囨。鍙樻洿
4. 鎵嬪伐楠屾敹鍛戒护
5. 椋庨櫓涓庡墿浣欑洸鍖?
寤鸿姣忓紶鍗＄殑浜や粯璇存槑缁熶竴閲囩敤锛?
```text
銆愪换鍔″崱銆慞0-XX
銆愯В鍐炽€戔€︹€?銆愬畬鎴愩€戔€︹€?銆愭祴璇曘€戔€︹€?銆愰闄┿€戔€︹€?銆愪笅涓€鍗°€戔€︹€?```

## 10. 褰撳墠鏈€閫傚悎绔嬪嵆寮€宸ョ殑鍗″崟

鑻ョ珛鍒昏 Codex 涓嬪垁锛屾帹鑽愮涓€鎵瑰紑宸ュ崱锛?
1. `P0-01 缁熶竴涓昏繍琛屾椂楠ㄦ灦`
2. `P0-02 /resume 鐪熼棴鐜痐
3. `P0-03 auth/config 涓婚摼淇涓庣粺涓€`
4. `P0-04 feature flag 杩愯鏃朵慨澶峘
5. `P0-05 review 鍛戒护浜у搧鍖朻

鐞嗙敱锛?
- 杩?5 寮犲崱鐩存帴鍐冲畾椤圭洰鏄惁浠庘€滃彲璺戜唬鐮佲€濊繘鍏モ€滃彲鏂藉伐浜у搧鈥?- 瀹冧滑閮藉睘浜庨珮纭畾鎬с€侀珮鏀剁泭銆佸彲鏈湴楠岃瘉鐨勪换鍔?- 鍏舵祴璇曞洖鎶ョ巼鏈€楂橈紝涓旇兘涓哄悗缁钩鍙板寲鍗″崟鎵竻闅滅

## 11. 鏂囨。缁存姢瑙勫垯

- 鑻ユ煇寮犱换鍔″崱杩涘叆寮€鍙戯紝鏂板鎵ц璁板綍鏃朵紭鍏堟洿鏂版湰鏂囦欢锛岃€屼笉鏄钩琛屾柊寤衡€滃悓涓婚灏忔枃妗ｂ€?- 鑻ヤ竴寮犱换鍔″崱琚户缁媶鍒嗭紝浣跨敤瀛愮紪鍙凤細
  - `P0-03A`
  - `P0-03B`
- 鑻ョ瓥鐣ュ彉鍖栧奖鍝嶄换鍔¤竟鐣岋紝鍏堟洿鏂颁笂娓告垬鐣ユ枃妗ｏ紝鍐嶅洖鍐欐湰鏂囦欢

## 12. 缁撹

鏈枃妗ｇ殑鐩爣涓嶆槸鈥滃垪寰呭姙浜嬮」鈥濓紝鑰屾槸寤虹珛涓€涓爺鍙戝彲鎵ц銆佹祴璇曞彲楠屾敹銆佺鐞嗗彲璺熻釜鐨勬柦宸ラ潰銆?
浠庣幇鍦ㄥ紑濮嬶紝鍚庣画鎵€鏈夊紑宸ュ缓璁兘搴斿熀浜庝换鍔″崱锛岃€屼笉鏄熀浜庢ā绯婃剰鍥俱€?
鎹㈣█涔嬶細

> 鍏堟寜鍗″紑宸ワ紝鍐嶆寜鍗￠獙灏革紝鍐嶆寜鍗℃帹杩涳紝涓嶅啀鍑劅瑙夊仛閲嶆瀯銆?
## 13. Execution Log (2026-04-29)

- Card: `P0-01 Runtime Backbone`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/main.py`
  - `claude_code/mcp/server.py`
- Test scripts landed:
  - `tests/test_main_runtime.py` (runtime bootstrap + mcp serve wiring coverage)
  - `tests/test_runtime_bootstrap.py` (entrypoint consistency + mcp registry injection)
- Not executed locally per release policy:
  - Unit/component/integration tests will be executed in Linux unified validation stage.

## 14. Execution Log (2026-04-29, P0-02)

- Card: `P0-02 /resume Runtime Closure`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/commands/compact/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/repl/__init__.py`
- Test scripts landed:
  - `tests/test_resume_runtime.py`
- Not executed locally per release policy:
  - Resume-related unit/component/integration checks will run in Linux unified validation stage.

## 15. Execution Log (2026-04-29, P0-03)

- Card: `P0-03 Auth/Config Runtime Unification`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/commands/auth/__init__.py`
- Test scripts landed:
  - `tests/test_commands_auth_runtime.py`
  - `tests/test_main_runtime.py` (auth key precedence coverage extension)
- Not executed locally per release policy:
  - Auth/config unit/component/integration checks will run in Linux unified validation stage.

## 16. Execution Log (2026-04-29, P0-04)

- Card: `P0-04 Feature Flag Runtime Repair`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/features.py`
- Test scripts landed:
  - `tests/test_features_runtime.py`
- Not executed locally per release policy:
  - Feature flag unit/component checks will run in Linux unified validation stage.

## 17. Execution Log (2026-04-29, P0-05)

- Card: `P0-05 Review Command Productization`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/commands/review/__init__.py`
  - `claude_code/services/review_service.py`
- Test scripts landed:
  - `tests/test_review_command_runtime.py`
- Not executed locally per release policy:
  - Review command unit/component/integration checks will run in Linux unified validation stage.

## 18. Execution Log (2026-04-29, P0-06)

- Card: `P0-06 Session/History/Memory Boundary Convergence`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/engine/query.py`
  - `claude_code/engine/session.py`
  - `claude_code/services/history_manager.py`
  - `claude_code/services/memory_service.py`
  - `claude_code/main.py`
- Test scripts landed:
  - `tests/test_session_history_memory_runtime.py`
  - `tests/test_context_builder_runtime.py` (boundary assertions extension)
  - `tests/test_main_runtime.py` (runtime service wiring extension)
- Not executed locally per release policy:
  - Session/history/memory unit/component/integration checks will run in Linux unified validation stage.

## 19. Execution Log (2026-04-29, P0-07)

- Card: `P0-07 Hooks Runtime Integration`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/hooks_manager.py`
  - `claude_code/commands/hooks/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/repl/__init__.py`
  - `claude_code/main.py`
- Test scripts landed:
  - `tests/test_hooks_runtime.py`
  - `tests/test_main_runtime.py` (hooks manager runtime bootstrap wiring update)
- Not executed locally per release policy:
  - Hooks runtime unit/component/integration checks will run in Linux unified validation stage.

## 20. Execution Log (2026-04-29, P0-09)

- Card: `P0-09 Temp Artifact Hygiene`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `tests/test_plugins_runtime.py`
  - `.gitignore`
- Test scripts landed:
  - `tests/test_plugins_runtime.py` (fixture teardown cleanup assertion + idempotent cleanup coverage)
- Not executed locally per release policy:
  - Plugin runtime cleanup and residue-isolation checks will run in Linux unified validation stage.

## 21. Execution Log (2026-04-29, P0-08)

- Card: `P0-08 Windows Bootstrap & Interpreter Probe Stabilization`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/main.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_doctor_runtime.py`
- Not executed locally per release policy:
  - Doctor interpreter-detection unit/component checks and Windows stub regression cases will run in Linux unified validation stage.

## 22. Execution Log (2026-04-29, P0-10)

- Card: `P0-10 Phase 0 Regression Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `pytest.ini`
  - `scripts/run_phase0_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_phase0_regression_contract.py`
- Not executed locally per release policy:
  - Phase 0 gate contract and curated regression-entry checks will run in Linux unified validation stage.

## 23. Execution Log (2026-04-29, P1-01)

- Card: `P1-01 Daemon/API Control Plane`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/server/control_plane.py`
  - `claude_code/server/__init__.py`
  - `claude_code/main.py`
  - `scripts/run_p1_control_plane_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_server_runtime.py` (`T1` schema validation, `T2` service behavior, `T3` client->server->runtime chain, `T4` daemon down/timeout/session-not-found)
  - `tests/test_main_runtime.py` (daemon CLI bootstrap wiring coverage)
- Not executed locally per release policy:
  - Daemon/API unit/component/integration/regression checks will run in Linux unified validation stage.

## 24. Execution Log (2026-04-29, P1-02)

- Card: `P1-02 Event Journal`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/event_journal.py`
  - `claude_code/services/__init__.py`
  - `claude_code/tasks/manager.py`
  - `claude_code/tasks/factory.py`
  - `claude_code/tasks/__init__.py`
  - `claude_code/engine/query.py`
  - `claude_code/server/control_plane.py`
  - `claude_code/main.py`
  - `scripts/run_p1_event_journal_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_event_journal_runtime.py` (`T1` schema/versioning, `T2` writer/reader correctness, `T3` query->tool->task event chain, `T4` partial write/corruption recovery)
  - `tests/test_server_runtime.py` (event list/replay daemon API coverage)
  - `tests/test_main_runtime.py` (runtime bootstrap wiring includes event journal)
- Not executed locally per release policy:
  - Event journal unit/component/integration/regression checks will run in Linux unified validation stage.

## 25. Execution Log (2026-04-29, P1-03)

- Card: `P1-03 SQLite Runtime State Backend`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/tasks/repository.py` (SQLite runtime repository + schema version/migration guard)
  - `claude_code/tasks/factory.py` (runtime backend default switched to `sqlite`)
  - `claude_code/tasks/__init__.py` (SQLite repository exports)
  - `claude_code/engine/session.py` (SQLite session store + manager constructor hook)
  - `claude_code/services/event_journal.py` (SQLite event journal + schema version/migration guard)
  - `claude_code/services/__init__.py` (SQLite event journal exports)
  - `claude_code/engine/query.py` (event journal duck-typing for backend-agnostic write path)
  - `claude_code/main.py` (runtime bootstrap switched to unified `.claude/runtime_state.db`)
  - `scripts/run_p1_sqlite_state_backend_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_sqlite_runtime_state_backend.py` (`T1` schema init/version guard, `T2` repository/session/event correctness, `T3` runtime chain wiring)
  - `tests/test_tasks_backend_contract.py` (SQLite repository contract + schema guard extension)
  - `tests/test_tasks_factory_runtime.py` (default runtime backend contract update to `sqlite`)
  - `tests/test_tasks_manager_runtime.py` (SQLite lifecycle persistence/recovery extension)
  - `tests/test_event_journal_runtime.py` (SQLite event journal schema/query/replay guard extension)
  - `tests/test_main_runtime.py` (runtime bootstrap mocks updated for SQLite state wiring)
- Not executed locally per release policy:
  - SQLite runtime state backend unit/component/integration/regression checks will run in Linux unified validation stage.

## 26. Execution Log (2026-04-30, P1-04)

- Card: `P1-04 Active Memory Runtime Integration`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/memory_service.py` (scoped memory namespaces + scope snapshot API)
  - `claude_code/engine/query.py` (active memory hit audit event + runtime memory scope propagation)
  - `claude_code/main.py` (system prompt active memory snapshot injection + runtime memory scope wiring)
  - `claude_code/tools/base.py` (tool context memory scope)
  - `claude_code/tools/agent/__init__.py` (agent-level memory scope propagation)
  - `claude_code/agents/builtin.py` (builtin agent memory scope defaults)
  - `scripts/run_p1_active_memory_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_memory_scope_runtime.py` (`T1` scope namespace isolation, scoped snapshot boundaries)
  - `tests/test_active_memory_runtime.py` (`T2` system-prompt memory injection, `T3` query memory-hit event chain, runtime scope propagation)
- Not executed locally per release policy:
  - Active memory unit/component/integration/regression checks will run in Linux unified validation stage.

## 27. Execution Log (2026-04-30, P1-05)

- Card: `P1-05 Hook/Permission/Audit Convergence`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/permissions.py` (structured permission evaluation reason output for audit chain)
  - `claude_code/services/hooks_manager.py` (hook result serialization helper)
  - `claude_code/engine/query.py` (permission request/decision events + hook execution audit events)
  - `scripts/run_p1_hook_permission_audit_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_hook_permission_audit_runtime.py` (`T2` permission+hook+audit linkage, `T3` tool execution audit chain, `T4` deny/error partial-failure path)
- Not executed locally per release policy:
  - Hook/permission/audit convergence unit/component/integration/regression checks will run in Linux unified validation stage.

## 28. Execution Log (2026-04-30, P1-06)

- Card: `P1-06 CLI Thin Client Migration`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/main.py` (daemon thin-client mode for query/pipe path, daemon-required hard-fail option, local fallback branch)
  - `scripts/run_p1_cli_thin_client_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_cli_daemon_thin_client_runtime.py` (`T2` client adapter mode resolution contract)
  - `tests/test_main_runtime.py` (daemon thin-client success/fallback/fail-fast and pipe-mode chain coverage)
- Not executed locally per release policy:
  - CLI thin-client adapter and daemon-fallback regression checks will run in Linux unified validation stage.

## 29. Execution Log (2026-04-30, P2-01)

- Card: `P2-01 Multi-Agent Supervisor`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/multi_agent_supervisor.py` (agent DAG scheduler, budget/timeout/retry policy, dependency artifact passing, parallel fan-out and aggregate close)
  - `claude_code/services/__init__.py` (supervisor exports)
  - `claude_code/tools/agent/__init__.py` (orchestrate mode + workflow schema + supervisor integration with structured artifact summary)
  - `scripts/run_p2_multi_agent_supervisor_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_multi_agent_supervisor_runtime.py` (`T1` graph cycle guard, `T2` budget/timeout state machine, `T3` parallel scheduling, `T4` retry-based failure recovery; plus agent tool orchestrate path and config error branch)
- Not executed locally per release policy:
  - Multi-agent supervisor unit/component/integration/regression checks will run in Linux unified validation stage.

## 30. Execution Log (2026-04-30, P2-02)

- Card: `P2-02 Artifact Bus & Conflict Convergence`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/artifact_bus.py` (artifact schema contract for patch/note/diff/report/finding, producer payload parsing, merge strategies `fail|append|replace`, conflict error path)
  - `claude_code/services/multi_agent_supervisor.py` (artifact bus integration for dependency artifact passing, workflow-level artifact snapshot, node artifact conflict/scheme failure handling)
  - `claude_code/services/__init__.py` (artifact bus exports)
  - `scripts/run_p2_artifact_bus_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_artifact_bus_runtime.py` (`T1` schema validation, `T2` producer/consumer dependency view, `T4` conflict-fail path, append merge behavior)
  - `tests/test_multi_agent_supervisor_runtime.py` (artifact bus summary extension + conflict merge failure branch in DAG execution)
- Not executed locally per release policy:
  - Artifact bus unit/component/integration/regression checks will run in Linux unified validation stage.

## 31. Execution Log (2026-04-30, P2-03)

- Card: `P2-03 IDE Integration (VS Code first)`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/server/control_plane.py` (added `/api/v1/ide/workspace` endpoint for IDE aggregate snapshot: diff, changed files, tasks, sessions, findings)
  - `claude_code/server/ide_adapter.py` (VS Code client adapter and normalized workspace snapshot model)
  - `claude_code/server/__init__.py` (IDE adapter exports)
  - `scripts/run_p2_ide_integration_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_ide_integration_runtime.py` (`T2` client protocol adapter normalization, `T3` IDE -> daemon core chain for diff/task/session/findings)
- Not executed locally per release policy:
  - IDE integration unit/component/integration/manual acceptance checks will run in Linux unified validation stage.

## 32. Execution Log (2026-04-30, P2-04)

- Card: `P2-04 GitHub/CI Workflow Agent`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/github_ci_workflow.py` (issue->plan->code->test->review->PR state machine, headless CI mode, command failure classification, structured workflow report)
  - `claude_code/server/control_plane.py` (added `POST /api/v1/workflows/github-ci` endpoint + client helper for workflow execution)
  - `claude_code/services/__init__.py` (GitHub/CI workflow service exports)
  - `scripts/run_p2_github_ci_workflow_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_github_ci_workflow_runtime.py` (`T2` workflow state machine, `T3` fake repo/fake PR main chain, `T4` permission-denied/repo-dirty/network-failure branches)
  - `tests/test_server_runtime.py` (daemon API route coverage for workflow success/failure mapping)
- Not executed locally per release policy:
  - GitHub/CI workflow unit/component/integration/regression checks will run in Linux unified validation stage.

## 33. Execution Log (2026-04-30, P2-05)

- Card: `P2-05 Org Policy & Audit`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/services/org_policy_audit.py` (org policy matcher, secret redaction, approval queue transitions, audit event query/report)
  - `claude_code/server/control_plane.py` (added org policy endpoints and client helpers: evaluate/approve/list/report)
  - `claude_code/services/__init__.py` (Org policy audit service exports)
  - `scripts/run_p2_org_policy_audit_gate.py`
  - `README.md`
- Test scripts landed:
  - `tests/test_org_policy_audit_runtime.py` (`T1` policy matcher+redaction, `T2` approval transitions, `T3` audit report chain, `T4` policy conflict block)
  - `tests/test_server_runtime.py` (daemon API coverage for org policy evaluate/approval/audit/report and failure mapping)
- Not executed locally per release policy:
  - Org policy/audit unit/component/integration/regression checks will run in Linux unified validation stage.

## 34. Execution Log (2026-04-30, P2-06)

- Card: `P2-06 Linux Unified Verification Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_linux_unified_gate.py` (aggregated Linux-stage command manifest for Phase 0 -> Phase 2 runtime chain)
  - `README.md` (added unified gate command entry)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (added P2-06 card + execution log)
- Test scripts landed:
  - `tests/test_linux_unified_gate_runtime.py` (`T1` manifest file existence contract, `T2` command generation order/format contract)
- Not executed locally per release policy:
  - Unified gate contract checks and all listed runtime tests will run in Linux unified validation stage.

## 35. Execution Log (2026-04-30, P2-07)

- Card: `P2-07 Agent Runtime Parity (sync/background)`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/tools/base.py` (ToolContext adds conversation/provider/task_manager/tool_registry fields for runtime propagation)
  - `claude_code/engine/query.py` (ToolContext now carries conversation/provider/task_manager/registry into tool execution path)
  - `claude_code/tasks/manager.py` (`create_agent_task` supports metadata injection for audit/replay)
  - `claude_code/tools/agent/__init__.py` (sync/background sub-agent parity: runtime provider/model resolution, registry propagation, task-manager reuse, background metadata contract)
  - `scripts/run_p2_agent_runtime_parity_gate.py`
  - `scripts/run_linux_unified_gate.py` (adds P2-07 regression test to unified manifest)
  - `README.md` (adds P2-07 gate command entry)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-07 card and execution log)
- Test scripts landed:
  - `tests/test_agent_background_context_runtime.py` (`T2` sync/background context parity, `T3` background task metadata audit fields, `T4` provider/model inheritance regression)
- Not executed locally per release policy:
  - Agent runtime parity unit/component/integration checks will run in Linux unified validation stage.

## 36. Execution Log (2026-04-30, P2-08)

- Card: `P2-08 Custom Agents Directory Loader`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/agents/loader.py` (custom agent markdown loader with YAML frontmatter parsing and cwd->git-root directory merge semantics)
  - `claude_code/tools/agent/__init__.py` (lazy custom agent load, custom>builtin resolution, and merged unknown-type availability hints)
  - `scripts/run_p2_custom_agents_loader_gate.py`
  - `scripts/run_linux_unified_gate.py` (adds P2-08 regression test to unified manifest)
  - `README.md` (adds P2-08 gate command entry)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-08 card and execution log)
- Test scripts landed:
  - `tests/test_custom_agents_loader_runtime.py` (`T1` frontmatter parsing, `T2` nested override merge, `T3` custom override builtin, `T4` invalid schema tolerance and unknown-type availability message)
- Not executed locally per release policy:
  - Custom-agent loader unit/component/integration checks will run in Linux unified validation stage.


## 37. Execution Log (2026-04-30, P2-09)

- Card: `P2-09 Linux Unified Execution Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_unified_execution_gate.py` (Linux-stage executor over unified manifest; supports dry-run/print/continue-on-failure/report-dir and writes junit + summary json)
  - `scripts/run_linux_unified_gate.py` (adds P2-09 execution gate contract test to unified manifest)
  - `README.md` (adds P2-09 execution gate command entries)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-09 card and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_unified_execution_gate_runtime.py` (`T1` unified manifest order contract, `T2` junit path and extra-args forwarding contract)
- Not executed locally per release policy:
  - Linux unified execution gate contract checks and full-suite execution will run in Linux validation stage.

## 38. Execution Log (2026-04-30, P2-10)

- Card: `P2-10 JetBrains IDE Integration`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `claude_code/server/ide_adapter.py` (added `JetBrainsClientAdapter` + `JetBrainsWorkspaceSnapshot` + findings->inspections mapping with severity highlight normalization)
  - `claude_code/server/__init__.py` (exports JetBrains adapter symbols)
  - `scripts/run_p2_jetbrains_ide_integration_gate.py`
  - `scripts/run_linux_unified_gate.py` (adds P2-10 adapter contract test to unified manifest)
  - `README.md` (adds P2-10 gate command)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-10 card and execution log)
- Test scripts landed:
  - `tests/test_p2_jetbrains_ide_integration_runtime.py` (`T1` adapter snapshot normalization, `T2` findings->inspection highlight mapping, `T4` line type coercion tolerance)
- Not executed locally per release policy:
  - JetBrains IDE adapter unit/component checks will run in Linux unified validation stage.

## 39. Execution Log (2026-04-30, P2-11)

- Card: `P2-11 Linux Sharded Execution Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_unified_execution_gate.py` (adds deterministic shard slicing via `--shard-total` + `--shard-index`, shard-aware dry-run header, shard metadata in summary payload)
  - `README.md` (adds Linux shard-parallel invocation example)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-11 card and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_unified_execution_gate_runtime.py` (adds shard slicing contract, invalid shard argument guards, summary shard metadata contract)
- Not executed locally per release policy:
  - P2-11 shard execution gate contract checks and full-suite execution will run in Linux validation stage.

## 40. Execution Log (2026-04-30, P2-12)

- Card: `P2-12 Linux Shard Aggregation Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_shard_aggregation_gate.py` (discovers shard summaries via direct path/glob/artifacts dir, validates summary schema, merges shard totals, emits merged summary and global pass/fail)
  - `scripts/run_linux_unified_gate.py` (adds P2-12 aggregation contract test to unified manifest)
  - `README.md` (adds Linux shard aggregation gate invocation examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-12 card and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_shard_aggregation_gate_runtime.py` (`T1` summary discovery dedupe, `T2` summary field validation, `T3` successful shard aggregation, `T4` missing-shard and total drift failure contract)
  - `tests/test_p2_linux_unified_execution_gate_runtime.py` (adds empty-shard summary payload contract used by aggregation stage)
- Not executed locally per release policy:
  - P2-12 aggregation gate contract checks and Linux multi-shard recovery validation will run in Linux unified validation stage.

## 41. Execution Log (2026-04-30, P2-13)

- Card: `P2-13 Linux Final Report Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_report_publish_gate.py` (loads merged shard summary, validates publish contract, emits final_report.json + final_report.md, enforces computed-vs-reported status consistency)
  - `scripts/run_linux_unified_gate.py` (adds P2-13 publish gate contract test to unified manifest)
  - `README.md` (adds P2-13 final report publish gate command examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-13 card and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_report_publish_gate_runtime.py` (`T1` merged summary required fields/types, `T2` happy-path payload contract, `T3` status mismatch failure contract, `T4` markdown report section contract)
- Not executed locally per release policy:
  - P2-13 publish gate contract checks and Linux final-report recovery validation will run in Linux unified validation stage.

## 42. Execution Log (2026-04-30, P2-14)

- Card: `P2-14 Linux Unified Pipeline Orchestration Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_unified_pipeline_gate.py` (orchestrates execution->aggregation->publish chain, supports stage skip controls, dry-run/print-commands, fail-fast, and pytest args forwarding to execution stage)
  - `scripts/run_linux_unified_gate.py` (adds P2-14 pipeline contract test to unified manifest)
  - `README.md` (adds P2-14 one-command Linux pipeline examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-14 card, dependency chain extension, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_unified_pipeline_gate_runtime.py` (`T1` default 3-stage command plan with execution summary feed, `T2` skip-execution external summary passthrough, `T3` all-stage-skip empty plan contract)
- Not executed locally per release policy:
  - P2-14 pipeline gate contract checks and Linux orchestrated recovery validation will run in Linux unified validation stage.

## 43. Execution Log (2026-04-30, P2-15)

- Card: `P2-15 Linux Shard Plan Generation Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_shard_plan_gate.py` (builds deterministic shard execution plan from unified manifest; emits per-shard report/summary/command payload; supports dry-run/print-commands/pytest args forwarding)
  - `scripts/run_linux_unified_gate.py` (adds P2-15 shard plan contract test to unified manifest)
  - `README.md` (adds P2-15 Linux shard plan command examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-15 card, dependency chain extension, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_shard_plan_gate_runtime.py` (`T1` deterministic shard slicing contract, `T2` command+args forwarding contract, `T3` invalid shard_total rejection contract)
- Not executed locally per release policy:
  - P2-15 shard plan gate contract checks and Linux fan-out orchestration validation will run in Linux unified validation stage.

## 44. Execution Log (2026-04-30, P2-16)

- Card: `P2-16 Linux CI Matrix Export Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_matrix_gate.py` (loads P2-15 shard plan, validates shard/total contract, emits CI-consumable matrix payload and summary-path collection, supports optional GitHub output export)
  - `scripts/run_linux_unified_gate.py` (adds P2-16 matrix gate contract test to unified manifest)
  - `README.md` (adds P2-16 CI matrix gate command examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-16 card, dependency chain extension, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_matrix_gate_runtime.py` (`T1` matrix include order/field contract, `T2` empty-shard filter contract, `T3` GitHub output value contract, `T4` totals mismatch rejection contract)
- Not executed locally per release policy:
  - P2-16 CI matrix export contract checks and Linux fan-out/fan-in orchestration validation will run in Linux unified validation stage.

## 45. Execution Log (2026-04-30, P2-17)

- Card: `P2-17 Linux CI Workflow Plan Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_plan_gate.py` (loads P2-16 ci_matrix, validates matrix/summary_paths contracts, emits CI-consumable workflow plan with fan-out matrix and fan-in aggregation/publish commands, supports optional GitHub output export)
  - `scripts/run_linux_unified_gate.py` (adds P2-17 workflow plan gate contract test to unified manifest)
  - `README.md` (adds P2-17 workflow plan gate command examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-17 card, dependency chain extension, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_plan_gate_runtime.py` (`T1` fan-out/fan-in payload contract, `T2` GitHub output contract, `T3` summary_paths order mismatch rejection, `T4` selected_shards mismatch rejection)
- Not executed locally per release policy:
  - P2-17 CI workflow plan contract checks and Linux fan-out/fan-in/final-publish orchestration validation will run in Linux unified validation stage.

## 46. Execution Log (2026-04-30, P2-18)

- Card: `P2-18 Linux CI Workflow YAML Render Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_yaml_gate.py` (loads P2-17 ci_workflow_plan, validates fan-out/fan-in contract, renders GitHub Actions workflow YAML, emits render metadata for audit traceability)
  - `scripts/run_linux_unified_gate.py` (adds P2-18 workflow YAML render contract test to unified manifest)
  - `README.md` (adds P2-18 workflow YAML gate command examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-18 card, dependency chain extension, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_yaml_gate_runtime.py` (`T1` workflow YAML fan-out/fan-in render contract, `T2` render metadata contract, `T3` summary_paths order mismatch rejection, `T4` selected_shards mismatch rejection)
- Not executed locally per release policy:
  - P2-18 workflow YAML render contract checks and Linux CI-end orchestration validation will run in Linux unified validation stage.

## 47. Execution Log (2026-04-30, P2-19)

- Card: `P2-19 Linux CI Workflow Drift Sync Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_sync_gate.py` (rebuilds expected workflow/metadata from P2-17 plan, validates drift against rendered artifacts, supports diff output and optional in-place sync write-back)
  - `scripts/run_linux_unified_gate.py` (adds P2-19 workflow sync contract test to unified manifest)
  - `README.md` (adds P2-19 drift check/sync command examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-19 card, dependency chain extension, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_sync_gate_runtime.py` (`T1` missing artifact drift contract, `T2` workflow content drift+diff contract, `T3` generated_at relaxed-mode contract, `T4` strict generated_at mismatch rejection)
- Not executed locally per release policy:
  - P2-19 workflow sync contract checks and Linux CI drift-governance validation will run in Linux unified validation stage.

## 48. Execution Log (2026-04-30, P2-20)

- Card: `P2-20 Linux CI Workflow Command Guard Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_command_guard_gate.py` (validates command string/parts integrity, script target + required flag contract, fan-out/fan-in path binding, optional canonical write-back)
  - `scripts/run_linux_unified_gate.py` (adds P2-20 command guard contract test to unified manifest)
  - `README.md` (adds P2-20 command guard gate invocation examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-20 card, dependency chain extension, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_command_guard_gate_runtime.py` (`T1` valid payload pass contract, `T2` command string/parts mismatch rejection + normalization contract, `T3` aggregation summary order mismatch rejection, `T4` publish path mismatch rejection)
- Not executed locally per release policy:
  - P2-20 command-integrity contract checks and Linux CI command-governance validation will run in Linux unified validation stage.

## 49. Execution Log (2026-04-30, P2-21)

- Card: `P2-21 Linux CI Workflow Governance Convergence Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_governance_gate.py` (aggregates P2-19 drift sync + P2-20 command guard + metadata lineage checks into one governance verdict and categorized failed_checks)
  - `scripts/run_linux_unified_gate.py` (adds P2-21 governance gate contract test to unified manifest)
  - `README.md` (adds P2-21 governance gate invocation examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-21 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_governance_gate_runtime.py` (`T1` full aligned pass contract, `T2` workflow drift failure category, `T3` command guard failure category, `T4` metadata lineage mismatch category)
- Not executed locally per release policy:
  - P2-21 governance convergence contract checks and Linux CI final-governance validation will run in Linux unified validation stage.

## 50. Execution Log (2026-04-30, P2-22)

- Card: `P2-22 Linux CI Workflow Governance Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_governance_publish_gate.py` (publishes P2-21 governance report into CI decision payload, markdown report, and optional GitHub outputs)
  - `scripts/run_linux_unified_gate.py` (adds P2-22 governance publish contract test to unified manifest)
  - `README.md` (adds P2-22 governance publish gate invocation examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-22 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_governance_publish_gate_runtime.py` (`T1` aligned governance pass contract, `T2` failed-checks deny-execution contract, `T3` failed_checks mismatch structural-failure contract, `T4` github-output field contract)
- Not executed locally per release policy:
  - P2-22 governance publish contract checks and Linux CI publish-stage validation will run in Linux unified validation stage.

## 51. Execution Log (2026-04-30, P2-23)

- Card: `P2-23 Linux CI Workflow Execution Decision Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_decision_gate.py` (converts P2-22 publish payload into execute/blocked decision contract with on-block exit policy, artifact-presence guard, markdown/json report, and optional GitHub outputs)
  - `scripts/run_linux_unified_gate.py` (adds P2-23 execution decision gate contract test to unified manifest)
  - `README.md` (adds P2-23 decision-gate usage examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-23 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_decision_gate_runtime.py` (`T1` aligned pass -> execute contract, `T2` failed-governance -> blocked contract, `T3` blocked+skip policy exit-code contract, `T4` github-output field contract)
- Not executed locally per release policy:
  - P2-23 execution-decision contract checks and Linux CI handoff validation will run in Linux unified validation stage.

## 52. Execution Log (2026-04-30, P2-24)

- Card: `P2-24 Linux CI Workflow Dispatch Readiness Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_dispatch_gate.py` (converts P2-23 execution decision payload into dispatch-ready contract, canonical gh workflow dispatch command, markdown/json reports, and optional GitHub outputs)
  - `scripts/run_linux_unified_gate.py` (adds P2-24 dispatch gate contract test to unified manifest)
  - `README.md` (adds P2-24 dispatch gate usage examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-24 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_dispatch_gate_runtime.py` (`T1` execute -> ready dispatch contract, `T2` blocked -> no-dispatch contract, `T3` decision contract mismatch rejection, `T4` github-output field contract)
- Not executed locally per release policy:
  - P2-24 dispatch-readiness contract checks and Linux CI dispatch handoff validation will run in Linux unified validation stage.

## 53. Execution Log (2026-04-30, P2-25)

- Card: `P2-25 Linux CI Workflow Dispatch Execution Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_dispatch_execution_gate.py` (validates P2-24 dispatch contract, executes ready dispatch command with timeout handling, and emits execution JSON/markdown/github-output contract)
  - `scripts/run_linux_unified_gate.py` (adds P2-25 dispatch execution gate contract test to unified manifest)
  - `README.md` (adds P2-25 dispatch execution gate usage examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-25 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_dispatch_execution_gate_runtime.py` (`T1` ready dry-run contract, `T2` blocked pass-through contract, `T3` command contract mismatch rejection, `T4` dispatch failure reason code contract, `T5` github-output field contract)
- Not executed locally per release policy:
  - P2-25 dispatch execution contract checks and Linux CI dispatch execution validation will run in Linux unified validation stage.

## 54. Execution Log (2026-04-30, P2-26)

- Card: `P2-26 Linux CI Workflow Full Pipeline Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (initially composed P2-17 -> P2-31 into single pipeline entry with stage skips, strategy passthrough, dry-run/print, fail-fast policy, terminal publish, release handoff, and release trigger stage)
  - `scripts/run_linux_unified_gate.py` (adds P2-26 pipeline gate contract test to unified manifest)
  - `README.md` (updates P2-26 one-command workflow pipeline usage examples to include terminal publish coverage)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-26 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (`T1` default stage-chain contract through release trigger, `T2` strategy passthrough contract, `T3` partial skip-stage chain contract, `T4` all-skip empty-plan contract, `T5` terminal-publish-only stage contract)
- Not executed locally per release policy:
  - P2-26 pipeline orchestration contract checks (including release trigger stage) and Linux CI end-to-end workflow gate validation will run in Linux unified validation stage.

## 55. Execution Log (2026-04-30, P2-27)

- Card: `P2-27 Linux CI Workflow Dispatch Traceability Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_dispatch_trace_gate.py` (builds dispatch trace contract from P2-25 report, extracts run reference, emits poll command, supports optional --poll-now run status query and GitHub outputs)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends pipeline stage chain with P2-27 dispatch trace stage and new trace control flags)
  - `scripts/run_linux_unified_gate.py` (adds P2-27 dispatch trace contract test to unified manifest)
  - `README.md` (adds P2-27 gate usage and updated pipeline examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-27 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_dispatch_trace_gate_runtime.py` (`T1` dispatched run reference extraction + poll command contract, `T2` missing run reference failure contract, `T3` blocked pass-through no-poll contract, `T4` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-27 stage presence and trace flag passthrough contract coverage)
- Not executed locally per release policy:
  - P2-27 dispatch trace contract checks and Linux CI run-tracking validation will run in Linux unified validation stage.

## 56. Execution Log (2026-04-30, P2-28)

- Card: `P2-28 Linux CI Workflow Dispatch Completion Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_dispatch_completion_gate.py` (converges P2-27 trace into completion verdict; supports poll loop with interval/max/timeout, optional allow-in-progress policy, and GitHub outputs)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain with P2-28 completion stage and new completion control flags/skip switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-28 completion contract test to unified manifest)
  - `README.md` (adds P2-28 gate usage and updates P2-26 full-chain examples to P2-28)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-28 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_dispatch_completion_gate_runtime.py` (`T1` success convergence contract, `T2` in-progress timeout contract, `T3` trace poll command mismatch rejection, `T4` github-output contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-28 stage presence and completion flag passthrough contract coverage)
- Not executed locally per release policy:
  - P2-28 dispatch completion contract checks and Linux CI terminal convergence validation will run in Linux unified validation stage.

## 57. Execution Log (2026-04-30, P2-29)

- Card: `P2-29 Linux CI Workflow Terminal Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_terminal_publish_gate.py` (converts P2-28 completion artifact into terminal publish verdict with promote/hold decision, contract mismatch guard, markdown/json/github-output contracts)
  - `scripts/run_linux_unified_gate.py` (adds P2-29 terminal publish contract test to unified manifest)
  - `README.md` (adds P2-29 terminal publish gate command examples)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-29 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_terminal_publish_gate_runtime.py` (`T1` success->publish/pass+promote contract, `T2` timeout+allow-in-progress->in_progress contract, `T3` success/exit mismatch->contract_failed contract, `T4` github-output field contract)
- Not executed locally per release policy:
  - P2-29 terminal publish contract checks and Linux CI terminal-release handoff validation will run in Linux unified validation stage.

## 58. Execution Log (2026-04-30, P2-30)

- Card: `P2-30 Linux CI Workflow Release Handoff Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_handoff_gate.py` (converts P2-29 terminal publish artifact into release handoff contract with promote/hold/reject action, target environment + channel semantics, contract mismatch guards, markdown/json/github-output outputs)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends pipeline stage chain to compose P2-17 -> P2-30 and adds release handoff output flags + skip switch + environment/channel passthrough)
  - `scripts/run_linux_unified_gate.py` (adds P2-30 release handoff contract test to unified manifest)
  - `README.md` (adds P2-30 release handoff gate invocation examples and updates P2-26 full-chain examples to P2-30)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-30 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_handoff_gate_runtime.py` (`T1` passed->ready_for_release contract, `T2` in_progress->awaiting_completion contract, `T3` publish contract mismatch->contract_failed contract, `T4` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-30 stage presence, environment/channel passthrough, and release-handoff-only stage contract coverage)
- Not executed locally per release policy:
  - P2-30 release handoff contract checks and Linux CI release-gate handoff validation will run in Linux unified validation stage.

## 59. Execution Log (2026-04-30, P2-31)

- Card: `P2-31 Linux CI Workflow Release Trigger Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_trigger_gate.py` (loads P2-30 handoff contract, validates trigger readiness, executes/dry-runs release command, emits trigger JSON/markdown/github-output report)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose P2-17 -> P2-31 and adds release-trigger flags/outputs/skip switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-31 release trigger contract test to unified manifest)
  - `README.md` (adds P2-31 gate usage and updates P2-26 full-chain examples to P2-31)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-31 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_trigger_gate_runtime.py` (`T1` ready_for_release dry-run contract, `T2` awaiting_completion pass-through contract, `T3` handoff contract mismatch rejection, `T4` trigger command failure convergence, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-31 stage presence, release-trigger flag passthrough, and release-trigger-only stage contract coverage)
- Not executed locally per release policy:
  - P2-31 release trigger contract checks and Linux CI release dispatch execution validation will run in Linux unified validation stage.

## 60. Execution Log (2026-04-30, P2-32)

- Card: `P2-32 Linux CI Workflow Release Traceability Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_trace_gate.py` (loads P2-31 release trigger artifact, validates trigger contract, extracts release run reference, emits optional poll command, supports optional --poll-now status query, and outputs JSON/markdown/github-output report)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-32`, adds release-trace outputs/flags/skip switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-32 release trace contract test to unified manifest)
  - `README.md` (adds P2-32 gate usage and updates P2-26 full-chain examples to P2-32)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-32 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_trace_gate_runtime.py` (`T1` triggered->run reference extraction contract, `T2` missing run reference failure contract, `T3` trigger_failed passthrough contract, `T4` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-32 stage presence, release-trace flag passthrough, and release-trace-only stage contract coverage)
- Not executed locally per release policy:
  - P2-32 release trace contract checks and Linux CI release run-tracking validation will run in Linux unified validation stage.

## 61. Execution Log (2026-04-30, P2-33)

- Card: `P2-33 Linux CI Workflow Release Completion Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_completion_gate.py` (converges P2-32 release trace into completion verdict; supports poll loop with interval/max/timeout, optional allow-in-progress policy, and GitHub outputs)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-33`, adds release-completion outputs/flags/skip switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-33 release completion contract test to unified manifest)
  - `README.md` (adds P2-33 gate usage and updates P2-26 full-chain examples to P2-33)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-33 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_completion_gate_runtime.py` (`T1` success convergence contract, `T2` in-progress timeout contract, `T3` release poll command mismatch rejection, `T4` github-output contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-33 stage presence, release-completion flag passthrough, and release-completion-only stage contract coverage)
- Not executed locally per release policy:
  - P2-33 release completion contract checks and Linux CI release terminal convergence validation will run in Linux unified validation stage.

## 62. Execution Log (2026-04-30, P2-34)

- Card: `P2-34 Linux CI Workflow Release Terminal Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_terminal_publish_gate.py` (converts P2-33 release completion artifact into release terminal publish verdict with finalize/hold decision, contract mismatch guard, markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-34`, adds release-terminal-publish outputs and `--skip-release-terminal-publish` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-34 release terminal publish contract test to unified manifest)
  - `README.md` (adds P2-34 gate usage and updates P2-26 full-chain examples to P2-34)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-34 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_terminal_publish_gate_runtime.py` (`T1` success->passed+finalize contract, `T2` timeout+allow-in-progress->in_progress contract, `T3` success/exit mismatch->contract_failed contract, `T4` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-34 stage presence, skip flag coverage, and release-terminal-publish-only stage contract)
- Verification performed without running tests:
  - `py -3 scripts/check_syntax.py --root scripts --json` passed.
  - `py -3 scripts/check_syntax.py --root tests --json` passed.
- Not executed locally per release policy:
  - P2-34 runtime contract checks and Linux CI release terminal publish validation will run in Linux unified validation stage.

## 63. Execution Log (2026-04-30, P2-35)

- Card: `P2-35 Linux CI Workflow Release Finalization Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_finalization_gate.py` (converts P2-34 release terminal publish artifact into final release closure contract with `finalize/hold/abort` decision, hold policy support, contract mismatch guard, markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-35`, adds release-finalization outputs and `--skip-release-finalization` switch, plus `--on-release-hold` policy passthrough)
  - `scripts/run_linux_unified_gate.py` (adds P2-35 release finalization contract test to unified manifest)
  - `README.md` (adds P2-35 gate usage and updates P2-26 full-chain examples to P2-35)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-35 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_finalization_gate_runtime.py` (`T1` passed->finalized contract, `T2` hold-policy-fail contract, `T3` publish contract mismatch->contract_failed contract, `T4` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-35 stage presence, hold-policy passthrough, and release-finalization-only stage contract)
- Not executed locally per release policy:
  - P2-35 runtime contract checks and Linux CI release finalization validation will run in Linux unified validation stage.

## 64. Execution Log (2026-04-30, P2-36)

- Card: `P2-36 Linux CI Workflow Release Closure Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_closure_gate.py` (converts P2-35 release finalization artifact into terminal release closure contract with `closed/pending/failed/contract_failed` status, `ship/hold/rollback` decision, consistency guard, markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-36`, adds release-closure outputs and `--skip-release-closure` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-36 release closure contract test to unified manifest)
  - `README.md` (adds P2-36 gate usage and updates P2-26 full-chain examples to P2-36)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-36 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_closure_gate_runtime.py` (`T1` finalized->closed contract, `T2` awaiting_release->pending contract, `T3` finalization mismatch->contract_failed contract, `T4` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-36 stage presence, skip flag coverage, and release-closure-only stage contract)
- Not executed locally per release policy:
  - P2-36 runtime contract checks and Linux CI release closure publish validation will run in Linux unified validation stage.

## 65. Execution Log (2026-04-30, P2-37)

- Card: `P2-37 Linux CI Workflow Release Archive Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_archive_gate.py` (converts P2-36 release closure artifact into terminal release archive contract with `ready/pending/failed/contract_failed` status, `publish/hold/block` decision, evidence-manifest existence checks, markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-37`, adds release-archive outputs and `--skip-release-archive` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-37 release archive contract test to unified manifest)
  - `README.md` (adds P2-37 gate usage and updates P2-26 full-chain examples to P2-37)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-37 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_archive_gate_runtime.py` (`T1` closed+evidence->ready contract, `T2` pending->hold contract, `T3` closure mismatch->contract_failed contract, `T4` missing evidence->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-37 stage presence and release-archive-only stage contract coverage)
- Not executed locally per release policy:
  - P2-37 runtime contract checks and Linux CI release evidence archive validation will run in Linux unified validation stage.

## 66. Execution Log (2026-04-30, P2-38)

- Card: `P2-38 Linux CI Workflow Release Verdict Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_verdict_gate.py` (converts P2-37 release archive artifact into terminal release verdict contract with `published/awaiting_archive/blocked/contract_failed` status, `ship/hold/block` decision, evidence consistency guard, markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-38`, adds release-verdict outputs and `--skip-release-verdict` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-38 release verdict contract test to unified manifest)
  - `README.md` (adds P2-38 gate usage and updates P2-26 full-chain examples to P2-38)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-38 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_verdict_gate_runtime.py` (`T1` ready->published contract, `T2` pending->awaiting_archive contract, `T3` archive mismatch->contract_failed contract, `T4` missing evidence->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-38 stage presence, skip flag coverage, and release-verdict-only stage contract)
- Not executed locally per release policy:
  - P2-38 runtime contract checks and Linux CI final release verdict convergence validation will run in Linux unified validation stage.

## 67. Execution Log (2026-04-30, Gate Contract Coverage Closure)

- Card: `Phase 1 Gate Runtime Contract Closure (P1-01 ~ P1-06)`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_linux_unified_gate.py` (extends Linux unified manifest with P1 gate runtime contract tests)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds closure execution log)
- Test scripts landed:
  - `tests/test_p1_control_plane_gate_runtime.py` (P1-01 manifest file existence + pytest command contract)
  - `tests/test_p1_event_journal_gate_runtime.py` (P1-02 manifest file existence + pytest command contract)
  - `tests/test_p1_sqlite_state_backend_gate_runtime.py` (P1-03 gate command chain + file existence contract)
  - `tests/test_p1_active_memory_gate_runtime.py` (P1-04 gate command chain + file existence contract)
  - `tests/test_p1_hook_permission_audit_gate_runtime.py` (P1-05 gate command chain + file existence contract)
  - `tests/test_p1_cli_thin_client_gate_runtime.py` (P1-06 gate command chain + file existence contract)
- Verification performed without running tests:
  - `py -3 scripts/check_syntax.py --root tests --json` passed.
  - `py -3 scripts/check_syntax.py --root scripts --json` passed.
- Not executed locally per release policy:
  - All new P1 gate runtime contract tests will be executed in Linux unified validation stage.

## 68. Execution Log (2026-05-01, P2-39)

- Card: `P2-39 Linux CI Workflow Release Incident Dispatch Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_incident_gate.py` (converts P2-38 release verdict artifact into terminal incident dispatch contract with `not_required/ready_dry_run/dispatched/dispatch_failed/contract_failed` status, verdict consistency guard, incident command execution fallback, markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-39`, adds release-incident outputs, incident command flags, and `--skip-release-incident` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-39 release incident contract test to unified manifest)
  - `README.md` (adds P2-39 gate usage and updates P2-26 full-chain examples to P2-39)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-39 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_incident_gate_runtime.py` (`T1` published->not_required contract, `T2` blocked->ready_dry_run contract, `T3` verdict mismatch->contract_failed contract, `T4` incident command failure convergence, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-39 stage presence, incident flag passthrough, and release-incident-only stage contract coverage)
- Not executed locally per release policy:
  - P2-39 runtime contract checks and Linux CI release incident dispatch validation will run in Linux unified validation stage.

## 69. Execution Log (2026-05-01, Gate Contract Coverage Closure II)

- Card: `Gate Runtime Contract Closure II (Phase 0 + P2 gate manifest coverage)`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `tests/test_phase0_gate_runtime.py` (adds contract coverage for `scripts/run_phase0_gate.py` manifest + pytest command builder)
  - `scripts/run_linux_unified_gate.py` (extends unified manifest to include:
    - `tests/test_phase0_gate_runtime.py`
    - `tests/test_linux_unified_gate_runtime.py`
    - `tests/test_p2_multi_agent_supervisor_gate_runtime.py`
    - `tests/test_p2_artifact_bus_gate_runtime.py`
    - `tests/test_p2_ide_integration_gate_runtime.py`
    - `tests/test_p2_github_ci_workflow_gate_runtime.py`
    - `tests/test_p2_org_policy_audit_gate_runtime.py`
    - `tests/test_p2_agent_runtime_parity_gate_runtime.py`
    - `tests/test_p2_custom_agents_loader_gate_runtime.py`
    - `tests/test_p2_jetbrains_ide_integration_gate_runtime.py`)
- Verification performed without running tests:
  - `py -3 scripts/check_syntax.py --root scripts --json` passed.
  - `py -3 scripts/check_syntax.py --root tests --json` passed.
  - Gate contract scan passed: `NO_MISSING_GATE_TESTS`.
  - Unified manifest scan passed: `NO_MISSING_UNIFIED_MANIFEST_TESTS`.
- Not executed locally per release policy:
  - All newly added gate runtime contract tests remain pending for Linux unified validation stage.

## 70. Execution Log (2026-05-01, P2-40)

- Card: `P2-40 Linux CI Workflow Release Terminal Verdict Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_terminal_verdict_gate.py` (converts P2-39 release incident artifact into terminal release verdict contract with `released/awaiting_archive/blocked_incident_ready_dry_run/blocked_incident_dispatched/blocked_incident_failed/blocked/contract_failed` status and `ship/hold/escalate/block` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-40`, adds release-terminal-verdict outputs, stage wiring, and `--skip-release-terminal-verdict` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-40 release terminal verdict contract test to unified manifest)
  - `README.md` (adds P2-40 gate usage and updates P2-26 full-chain examples to P2-40)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-40 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_terminal_verdict_gate_runtime.py` (`T1` published->released contract, `T2` blocked+ready_dry_run->blocked_incident_ready_dry_run contract, `T3` verdict/incident mismatch->contract_failed contract, `T4` evidence missing->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-40 stage presence, command path assertions, skip flag propagation, and release-terminal-verdict-only stage contract coverage)
- Not executed locally per release policy:
  - P2-40 runtime contract checks and Linux CI final terminal verdict convergence validation will run in Linux unified validation stage.

## 71. Execution Log (2026-05-01, P2-41)

- Card: `P2-41 Linux CI Workflow Release Delivery Closure Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_delivery_gate.py` (converts P2-40 release terminal verdict artifact into final delivery contract with `shipped/pending_follow_up/blocked_incident/blocked_incident_failed/blocked/contract_failed` status and `deliver/hold/escalate/block` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-41`, adds release-delivery outputs, stage wiring, and `--skip-release-delivery` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-41 release delivery contract test to unified manifest)
  - `README.md` (adds P2-41 gate usage and updates P2-26 full-chain examples to P2-41)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-41 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_delivery_gate_runtime.py` (`T1` released->shipped contract, `T2` blocked_incident_ready_dry_run->blocked_incident contract, `T3` terminal/incident mismatch->contract_failed contract, `T4` evidence missing->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-41 stage presence, command path assertions, skip flag propagation, and release-delivery-only stage contract coverage)
- Not executed locally per release policy:
  - P2-41 runtime contract checks and Linux CI final delivery closure convergence validation will run in Linux unified validation stage.

## 72. Execution Log (2026-05-01, P2-42)

- Card: `P2-42 Linux CI Workflow Release Delivery Terminal Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_delivery_terminal_publish_gate.py` (converts P2-41 release delivery artifact into terminal publish contract with `published/pending_follow_up/blocked/contract_failed` status and `announce_release/announce_hold/announce_blocker/abort_publish` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-42`, adds release-delivery-terminal-publish outputs, stage wiring, and `--skip-release-delivery-terminal-publish` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-42 release delivery terminal publish contract test to unified manifest)
  - `README.md` (adds P2-42 gate usage and updates P2-26 full-chain examples to P2-42)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-42 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_delivery_terminal_publish_gate_runtime.py` (`T1` shipped->published contract, `T2` blocked_incident->blocked contract, `T3` delivery/incident mismatch->contract_failed contract, `T4` evidence missing->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-42 stage presence, command path assertions, skip flag propagation, and release-delivery-terminal-publish-only stage contract coverage)
- Not executed locally per release policy:
  - P2-42 runtime contract checks and Linux CI final terminal publish convergence validation will run in Linux unified validation stage.

## 73. Execution Log (2026-05-01, P2-43)

- Card: `P2-43 Linux CI Workflow Release Delivery Final Verdict Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_delivery_final_verdict_gate.py` (converts P2-42 release delivery terminal publish artifact into final verdict contract with `completed/requires_follow_up/blocked/contract_failed` status and `close_release/open_follow_up/escalate_blocker/abort_close` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-43`, adds release-delivery-final-verdict outputs, stage wiring, and `--skip-release-delivery-final-verdict` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-43 release delivery final verdict contract test to unified manifest)
  - `README.md` (adds P2-43 gate usage and updates P2-26 full-chain examples to P2-43)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-43 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_delivery_final_verdict_gate_runtime.py` (`T1` published->completed contract, `T2` pending_follow_up->requires_follow_up contract, `T3` terminal/delivery/incident mismatch->contract_failed contract, `T4` evidence missing->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-43 stage presence, command path assertions, skip flag propagation, and release-delivery-final-verdict-only stage contract coverage)
- Not executed locally per release policy:
  - P2-43 runtime contract checks and Linux CI final verdict convergence validation will run in Linux unified validation stage.

## 74. Execution Log (2026-05-01, P2-44)

- Card: `P2-44 Linux CI Workflow Release Follow-Up Dispatch Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_follow_up_dispatch_gate.py` (converts P2-43 release delivery final verdict artifact into follow-up dispatch contract with `closed/follow_up_required/escalated/contract_failed` status and `no_action/dispatch_follow_up/dispatch_escalation/abort_dispatch` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-44`, adds release-follow-up-dispatch outputs, stage wiring, and `--skip-release-follow-up-dispatch` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-44 release follow-up dispatch contract test to unified manifest)
  - `README.md` (adds P2-44 gate usage and updates P2-26 full-chain examples to P2-44)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-44 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_follow_up_dispatch_gate_runtime.py` (`T1` completed->closed contract, `T2` requires_follow_up->follow_up_required contract, `T3` final-verdict mismatch->contract_failed contract, `T4` evidence missing->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-44 stage presence, command path assertions, skip flag propagation, and release-follow-up-dispatch-only stage contract coverage)
- Not executed locally per release policy:
  - P2-44 runtime contract checks and Linux CI follow-up dispatch convergence validation will run in Linux unified validation stage.

## 75. Execution Log (2026-05-01, P2-45)

- Card: `P2-45 Linux CI Workflow Release Follow-Up Closure Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_follow_up_closure_gate.py` (converts P2-44 release follow-up dispatch artifact into follow-up closure contract with `closed/queued_dry_run/queued/queue_failed/contract_failed` status and `no_action/queue_follow_up/queue_escalation/abort_queue` decision, plus consistency guards, optional follow-up queue command execution, markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-45`, adds release-follow-up-closure outputs, stage wiring, follow-up command flags, and `--skip-release-follow-up-closure` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-45 release follow-up closure contract test to unified manifest)
  - `README.md` (adds P2-45 gate usage and updates P2-26 full-chain examples to P2-45)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-45 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_follow_up_closure_gate_runtime.py` (`T1` closed->no_action contract, `T2` follow_up_required->queued_dry_run contract, `T3` dispatch mismatch->contract_failed contract, `T4` follow-up queue command failure->queue_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-45 stage presence, command path assertions, follow-up flag propagation, and release-follow-up-closure-only stage contract coverage)
- Not executed locally per release policy:
  - P2-45 runtime contract checks and Linux CI follow-up closure convergence validation will run in Linux unified validation stage.

## 76. Execution Log (2026-05-01, P2-46)

- Card: `P2-46 Linux CI Workflow Release Follow-Up Terminal Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate.py` (converts P2-45 release follow-up closure artifact into terminal publish contract with `published/pending_queue/queue_failed/contract_failed` status and `announce_closed/announce_queued/announce_pending_queue/announce_queue_failure/abort_publish` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-46`, adds release-follow-up-terminal-publish outputs, stage wiring, and `--skip-release-follow-up-terminal-publish` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-46 release follow-up terminal publish contract test to unified manifest)
  - `README.md` (adds P2-46 gate usage and updates P2-26 full-chain examples to P2-46)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-46 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_follow_up_terminal_publish_gate_runtime.py` (`T1` closed->published contract, `T2` queued_dry_run->pending_queue contract, `T3` closure mismatch->contract_failed contract, `T4` queue_failed->queue_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-46 stage presence, command path assertions, skip flag propagation, and release-follow-up-terminal-publish-only stage contract coverage)
- Not executed locally per release policy:
  - P2-46 runtime contract checks and Linux CI follow-up terminal publish convergence validation will run in Linux unified validation stage.

## 77. Execution Log (2026-05-01, P2-47)

- Card: `P2-47 Linux CI Workflow Release Follow-Up Final Verdict Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_follow_up_final_verdict_gate.py` (converts P2-46 release follow-up terminal publish artifact into final follow-up verdict contract with `completed/requires_follow_up/blocked/contract_failed` status and `close_follow_up/keep_follow_up_open/escalate_queue_failure/abort_close` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-47`, adds release-follow-up-final-verdict outputs, stage wiring, and `--skip-release-follow-up-final-verdict` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-47 release follow-up final verdict contract test to unified manifest)
  - `README.md` (adds P2-47 gate usage and updates P2-26 full-chain examples to P2-47)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-47 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_follow_up_final_verdict_gate_runtime.py` (`T1` published+announce_closed->completed contract, `T2` pending_queue->requires_follow_up contract, `T3` queue_failed->blocked contract, `T4` contract mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-47 stage presence, command path assertions, skip flag propagation, and release-follow-up-final-verdict-only stage contract coverage)
- Not executed locally per release policy:
  - P2-47 runtime contract checks and Linux CI follow-up final verdict convergence validation will run in Linux unified validation stage.

## 78. Execution Log (2026-05-01, P2-48)

- Card: `P2-48 Linux CI Workflow Release Final Outcome Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_outcome_gate.py` (converges P2-43 + P2-47 final verdict artifacts into one terminal release outcome contract with `released/released_with_follow_up/blocked/contract_failed` status and `ship_and_close/ship_with_follow_up_open/escalate_blocker/abort_outcome` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-48`, adds release-final-outcome outputs, stage wiring, and `--skip-release-final-outcome` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-48 release final outcome contract test to unified manifest)
  - `README.md` (adds P2-48 gate usage and updates P2-26 full-chain examples to P2-48)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-48 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_outcome_gate_runtime.py` (`T1` released contract, `T2` released_with_follow_up contract, `T3` blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-48 stage presence, command path assertions, skip flag propagation, and release-final-outcome-only stage contract coverage)
- Not executed locally per release policy:
  - P2-48 runtime contract checks and Linux CI final release outcome convergence validation will run in Linux unified validation stage.

## 79. Execution Log (2026-05-01, P2-49)

- Card: `P2-49 Linux CI Workflow Release Final Terminal Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_terminal_publish_gate.py` (converges P2-48 final outcome artifact into terminal publish contract with `published/published_with_follow_up/blocked/contract_failed` status and `announce_release_closure/announce_release_with_follow_up/announce_blocker/abort_publish` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-49`, adds release-final-terminal-publish outputs, stage wiring, and `--skip-release-final-terminal-publish` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-49 release final terminal publish contract test to unified manifest)
  - `README.md` (adds P2-49 gate usage and updates P2-26 full-chain examples to P2-49)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-49 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_terminal_publish_gate_runtime.py` (`T1` released->published contract, `T2` released_with_follow_up->published_with_follow_up contract, `T3` blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-49 stage presence, command path assertions, skip flag propagation, and release-final-terminal-publish-only stage contract coverage)
- Not executed locally per release policy:
  - P2-49 runtime contract checks and Linux CI final terminal publish convergence validation will run in Linux unified validation stage.

## 80. Execution Log (2026-05-01, P2-50)

- Card: `P2-50 Linux CI Workflow Release Final Handoff Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_handoff_gate.py` (converges P2-49 final terminal publish artifact into release handoff contract with `completed/completed_with_follow_up/blocked/contract_failed` status and `handoff_release_closure/handoff_release_with_follow_up/handoff_blocker/abort_handoff` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-50`, adds release-final-handoff outputs, stage wiring, and `--skip-release-final-handoff` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-50 release final handoff contract test to unified manifest)
  - `README.md` (adds P2-50 gate usage and updates P2-26 full-chain examples to P2-50)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-50 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_handoff_gate_runtime.py` (`T1` published->completed contract, `T2` published_with_follow_up->completed_with_follow_up contract, `T3` blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-50 stage presence, command path assertions, skip flag propagation, and release-final-handoff-only stage contract coverage)
- Not executed locally per release policy:
  - P2-50 runtime contract checks and Linux CI final handoff convergence validation will run in Linux unified validation stage.

## 81. Execution Log (2026-05-01, P2-51)

- Card: `P2-51 Linux CI Workflow Release Final Closure Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_closure_gate.py` (converges P2-50 final handoff artifact into release closure contract with `closed/closed_with_follow_up/blocked/contract_failed` status and `close_release/close_with_follow_up/close_blocker/abort_close` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-51`, adds release-final-closure outputs, stage wiring, and `--skip-release-final-closure` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-51 release final closure contract test to unified manifest)
  - `README.md` (adds P2-51 gate usage and updates P2-26 full-chain examples to P2-51)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-51 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_closure_gate_runtime.py` (`T1` completed->closed contract, `T2` completed_with_follow_up->closed_with_follow_up contract, `T3` blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-51 stage presence, command path assertions, skip flag propagation, and release-final-closure-only stage contract coverage)
- Not executed locally per release policy:
  - P2-51 runtime contract checks and Linux CI final closure convergence validation will run in Linux unified validation stage.

## 82. Execution Log (2026-05-01, P2-52)

- Card: `P2-52 Linux CI Workflow Release Final Closure Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_closure_publish_gate.py` (converges P2-51 release final closure artifact into final closure publish contract with `published/published_with_follow_up/blocked/contract_failed` status and `announce_release_closed/announce_release_closed_with_follow_up/announce_release_blocker/abort_publish` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-52`, adds release-final-closure-publish outputs, stage wiring, and `--skip-release-final-closure-publish` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-52 release final closure publish contract test to unified manifest)
  - `README.md` (adds P2-52 gate usage and updates P2-26 full-chain examples to P2-52)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-52 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_closure_publish_gate_runtime.py` (`T1` closed->published contract, `T2` closed_with_follow_up->published_with_follow_up contract, `T3` blocked->blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-52 stage presence, command path assertions, skip flag propagation, and release-final-closure-publish-only stage contract coverage)
- Not executed locally per release policy:
  - P2-52 runtime contract checks and Linux CI final closure publish convergence validation will run in Linux unified validation stage.

## 83. Execution Log (2026-05-01, P2-53)

- Card: `P2-53 Linux CI Workflow Release Final Archive Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_archive_gate.py` (converges P2-52 release final closure publish artifact into final archive contract with `archived/archived_with_follow_up/blocked/contract_failed` status and `archive_release_closed/archive_release_closed_with_follow_up/archive_release_blocker/abort_archive` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-53`, adds release-final-archive outputs, stage wiring, and `--skip-release-final-archive` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-53 release final archive contract test to unified manifest)
  - `README.md` (adds P2-53 gate usage and updates P2-26 full-chain examples to P2-53)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-53 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_archive_gate_runtime.py` (`T1` published->archived contract, `T2` published_with_follow_up->archived_with_follow_up contract, `T3` blocked->blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-53 stage presence, command path assertions, skip flag propagation, and release-final-archive-only stage contract coverage)
- Not executed locally per release policy:
  - P2-53 runtime contract checks and Linux CI final archive convergence validation will run in Linux unified validation stage.

## 84. Execution Log (2026-05-01, P2-54)

- Card: `P2-54 Linux CI Workflow Release Final Verdict Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_verdict_gate.py` (converges P2-53 final archive artifact into final verdict contract with `released/released_with_follow_up/blocked/contract_failed` status and `ship_release/ship_release_with_follow_up/escalate_release_blocker/abort_verdict` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-54`, adds release-final-verdict outputs, stage wiring, and `--skip-release-final-verdict` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-54 release final verdict contract test to unified manifest)
  - `README.md` (adds P2-54 gate usage and updates P2-26 full-chain examples to P2-54)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-54 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_verdict_gate_runtime.py` (`T1` archived->released contract, `T2` archived_with_follow_up->released_with_follow_up contract, `T3` blocked->blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-54 stage presence, command path assertions, skip flag propagation, and release-final-verdict-only stage contract coverage)
- Not executed locally per release policy:
  - P2-54 runtime contract checks and Linux CI final verdict convergence validation will run in Linux unified validation stage.

## 85. Execution Log (2026-05-01, P2-55)

- Card: `P2-55 Linux CI Workflow Release Final Verdict Publish Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_verdict_publish_gate.py` (converges P2-54 final verdict artifact into final verdict publish contract with `published/published_with_follow_up/blocked/contract_failed` status and `announce_release_shipped/announce_release_shipped_with_follow_up/announce_release_blocker/abort_publish` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-55`, adds release-final-verdict-publish outputs, stage wiring, and `--skip-release-final-verdict-publish` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-55 release final verdict publish contract test to unified manifest)
  - `README.md` (adds P2-55 gate usage and updates P2-26 full-chain examples to P2-55)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency chain extension, P2-55 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_verdict_publish_gate_runtime.py` (`T1` released->published contract, `T2` released_with_follow_up->published_with_follow_up contract, `T3` blocked->blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-55 stage presence, command path assertions, skip flag propagation, and release-final-verdict-publish-only stage contract coverage)
- Not executed locally per release policy:
  - P2-55 runtime contract checks and Linux CI final verdict publish convergence validation will run in Linux unified validation stage.

## 86. Execution Log (2026-05-01, P2-56)

- Card: `P2-56 Linux CI Workflow Release Final Publish Archive Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_release_final_publish_archive_gate.py` (converges P2-55 final verdict publish artifact into final publish archive contract with `archived/archived_with_follow_up/blocked/contract_failed` status and `archive_release_shipped/archive_release_shipped_with_follow_up/archive_release_blocker/abort_archive` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-56`, adds release-final-publish-archive outputs, stage wiring, and `--skip-release-final-publish-archive` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-56 release final publish archive contract test to unified manifest)
  - `README.md` (adds P2-56 gate usage and updates P2-26 full-chain examples to P2-56)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency-chain extension, P2-56 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_release_final_publish_archive_gate_runtime.py` (`T1` published->archived contract, `T2` published_with_follow_up->archived_with_follow_up contract, `T3` blocked->blocked contract, `T4` mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-56 stage presence, command path assertions, skip flag propagation, and release-final-publish-archive-only stage contract coverage)
- Not executed locally per release policy:
  - P2-56 runtime contract checks and Linux CI final publish archive convergence validation will run in Linux unified validation stage.

## 87. Execution Log (2026-05-01, P2-57)

- Card: `P2-57 Linux Gate Manifest Drift Closure Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_gate_manifest_drift_gate.py` (adds closure guard that scans `run_*_gate.py` -> `test_*_gate_runtime.py` mapping and validates Linux unified manifest coverage + orphan manifest entries, emits JSON/Markdown + GitHub outputs)
  - `scripts/run_linux_unified_gate.py` (adds P2-57 runtime contract test to Linux unified manifest)
  - `README.md` (adds P2-57 standalone usage while keeping P2-26 full-chain wording as `P2-17 -> P2-56`)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency-chain extension, P2-57 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_gate_manifest_drift_gate_runtime.py` (`T1` gate scan include/exclude contract, `T2` runtime-test mapping contract, `T3` baseline drift report passed contract, `T4` github-output field contract)
- Verification performed (without running tests):
  - `py -3 scripts/check_syntax.py --root scripts --json` passed.
  - `py -3 scripts/check_syntax.py --root tests --json` passed.
- Not executed locally per release policy:
  - P2-57 runtime contract checks and Linux gate drift closure convergence validation will run in Linux unified validation stage.

## 88. Execution Log (2026-05-01, P2-58)

- Card: `P2-58 Linux CI Workflow Pipeline Closure to P2-57`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain description to `P2-17 -> P2-57`, wires `workflow_gate_manifest_drift` stage to call `scripts/run_p2_linux_gate_manifest_drift_gate.py`, adds `--gate-manifest-drift-json-output` / `--gate-manifest-drift-markdown-output`, and adds `--skip-gate-manifest-drift`)
  - `README.md` (updates P2-26 full-chain wording to `P2-17 -> P2-57` and adds P2-57-only pipeline command)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds P2-58 execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-57 stage presence in default/partial chain, command assertions for drift-stage output paths, skip-flag propagation, and P2-57-only stage contract coverage)
- Verification performed (without running tests):
  - `py -3 scripts/check_syntax.py --root scripts --json` passed.
  - `py -3 scripts/check_syntax.py --root tests --json` passed.
- Not executed locally per release policy:
  - P2-58 runtime contract checks and Linux CI workflow pipeline closure convergence validation will run in Linux unified validation stage.

## 89. Execution Log (2026-05-01, P2-59)

- Card: `P2-59 Linux CI Workflow Terminal Verdict Closure Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_terminal_verdict_gate.py` (converges P2-56 release final publish archive report and P2-57 gate manifest drift report into one terminal verdict contract with `ready_for_linux_validation/ready_with_follow_up_for_linux_validation/blocked/contract_failed` status and `proceed_linux_validation/proceed_linux_validation_with_follow_up/halt_linux_validation_blocker/abort_linux_validation` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-59`, adds terminal-verdict outputs, stage wiring, and `--skip-terminal-verdict` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-59 terminal verdict contract test to unified manifest)
  - `README.md` (adds P2-59 standalone usage, updates P2-26 full-chain examples to `P2-17 -> P2-59`, and adds P2-59-only pipeline command)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency-chain extension, P2-59 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_terminal_verdict_gate_runtime.py` (`T1` archived+drift-passed->ready contract, `T2` archived-with-follow-up+drift-passed->ready-with-follow-up contract, `T3` blocked+drift-passed->blocked contract, `T4` archive mismatch or drift-failed->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-59 stage presence in default/partial chain, command assertions for terminal-verdict report paths, compatibility propagation for `skip_terminal_verdict`, and P2-59-only stage contract coverage)
- Verification performed (without running tests):
  - `py -3 scripts/check_syntax.py --root scripts --json` passed.
  - `py -3 scripts/check_syntax.py --root tests --json` passed.
- Not executed locally per release policy:
  - P2-59 runtime contract checks and Linux CI terminal verdict closure convergence validation will run in Linux unified validation stage.

## 90. Execution Log (2026-05-01, P2-60)

- Card: `P2-60 Linux CI Workflow Linux Validation Dispatch Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_linux_validation_dispatch_gate.py` (converges P2-59 terminal verdict into Linux validation dispatch contract with `ready_dry_run/ready_with_follow_up_dry_run/dispatched/dispatch_failed/blocked/contract_failed` status and `dispatch_linux_validation/dispatch_linux_validation_with_follow_up/hold_linux_validation_blocker/abort_linux_validation_dispatch` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-60`, adds Linux validation dispatch outputs, stage wiring, timeout flag, and `--skip-linux-validation-dispatch` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-60 Linux validation dispatch contract test to unified manifest)
  - `README.md` (adds P2-60 standalone usage, updates full-chain examples to `P2-17 -> P2-60`, and adds P2-60-only pipeline command)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency-chain extension, P2-60 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_linux_validation_dispatch_gate_runtime.py` (`T1` ready->ready_dry_run contract, `T2` ready_with_follow_up->ready_with_follow_up_dry_run contract, `T3` blocked->blocked contract, `T4` mismatch/drift/evidence issue->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-60 stage presence in default/partial chain, command assertions for Linux validation dispatch paths/timeout, and P2-60-only stage contract coverage)
- Verification performed (without running tests):
  - `py -3 scripts/check_syntax.py --root scripts --json` passed.
  - `py -3 scripts/check_syntax.py --root tests --json` passed.
- Not executed locally per release policy:
  - No pytest execution; all new/updated runtime contract tests remain pending for Linux unified validation stage.

## 91. Execution Log (2026-05-01, P2-61)

- Card: `P2-61 Linux CI Workflow Linux Validation Verdict Gate`
- Status: `implemented` (Linux full-suite verification pending)
- Code landed:
  - `scripts/run_p2_linux_ci_workflow_linux_validation_verdict_gate.py` (converges P2-60 Linux validation dispatch artifact into one final Linux validation verdict contract with `validated/validated_with_follow_up/validation_failed/blocked/contract_failed` status and `accept_linux_validation/accept_linux_validation_with_follow_up/escalate_linux_validation_failure/hold_linux_validation_blocker/abort_linux_validation_verdict` decision, plus consistency guards and markdown/json/github-output contracts)
  - `scripts/run_p2_linux_ci_workflow_pipeline_gate.py` (extends stage chain to compose `P2-17 -> P2-61`, adds Linux validation verdict outputs, stage wiring, and `--skip-linux-validation-verdict` switch)
  - `scripts/run_linux_unified_gate.py` (adds P2-61 Linux validation verdict contract test to unified manifest)
  - `README.md` (adds P2-61 standalone usage, updates full-chain examples to `P2-17 -> P2-61`, and adds P2-61-only pipeline command)
  - `docs/current/architecture/EXECUTION_TASK_CARDS_2026-04-29.md` (adds dependency-chain extension, P2-61 card, and execution log)
- Test scripts landed:
  - `tests/test_p2_linux_ci_workflow_linux_validation_verdict_gate_runtime.py` (`T1` ready_dry_run->validated contract, `T2` ready_with_follow_up_dry_run->validated_with_follow_up contract, `T3` dispatch_failed->validation_failed contract, `T4` dispatch/evidence mismatch->contract_failed contract, `T5` github-output field contract)
  - `tests/test_p2_linux_ci_workflow_pipeline_gate_runtime.py` (adds P2-61 stage presence in default/partial chain, command assertions for Linux validation verdict paths, skip propagation for `skip_linux_validation_verdict`, and P2-61-only stage contract coverage)
- Verification performed (without running tests):
  - `py -3 scripts/check_syntax.py --root scripts --json` passed.
  - `py -3 scripts/check_syntax.py --root tests --json` passed.
- Not executed locally per release policy:
  - No pytest execution; all new/updated runtime contract tests remain pending for Linux unified validation stage.
