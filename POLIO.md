# POLIO.md — This site

The hand-off for a code chat opened on this repository. The Builder writes it at every Go live, from the site as it was pressed; the same site writes the same file. Read it first: what the site is, where each part lives, what already moves, and what still needs code.

Every part is an element whose `id` is the part's id, so `document.getElementById("<id>")` finds it on its page. The pages are static HTML; the site's stylesheet is `assets/site.css`, and the features it runs are `assets/features/*.js`. TASKS.md lists the owner's own asks; AGENTS.md says how to add a feature so the Builder can take it back.

## 1. Style

### Colours

The six roles, written in `assets/site.css` as `var(--<role>)`:

| Role | Colour | CSS |
|---|---|---|
| bg | `#fdf0dc` | `var(--bg)` |
| surface | `#1a0f0b` | `var(--surface)` |
| text | `#1a0f0b` | `var(--text)` |
| muted | `#6b5544` | `var(--muted)` |
| accent | `#b8ff6a` | `var(--accent)` |
| highlight | `#0000ee` | `var(--highlight)` |

Every colour the parts wear, most used first:

| Colour | Parts | Text | Fill | Border | Shadow |
|---|---|---|---|---|---|
| `#1a0f0b` | 317 | 287 | 28 | 89 | 59 |
| `#111111` | 286 | 286 | 0 | 0 | 0 |
| `#b8ff6a` | 91 | 91 | 2 | 0 | 0 |
| `#000000` | 54 | 36 | 3 | 23 | 15 |
| `#f3d440` | 36 | 0 | 36 | 0 | 0 |
| `#fff3b0` | 35 | 0 | 35 | 0 | 0 |
| `rgba(160, 255, 90, 0.7)` | 30 | 0 | 0 | 0 | 30 |
| `#efefef` | 28 | 0 | 28 | 0 | 0 |
| `#0000ee` | 27 | 27 | 0 | 0 | 0 |
| `#ffffff` | 26 | 0 | 26 | 0 | 0 |
| `#ef9043` | 24 | 12 | 12 | 0 | 0 |
| `#6b5544` | 15 | 15 | 0 | 0 | 0 |
| `#d9702e` | 15 | 12 | 3 | 0 | 0 |
| `rgba(160, 255, 90, 0.9)` | 15 | 0 | 0 | 0 | 15 |
| `#767676` | 13 | 0 | 0 | 13 | 0 |
| `#fff8ec` | 13 | 0 | 13 | 0 | 0 |
| `#ffb36b` | 12 | 0 | 12 | 0 | 0 |
| `rgb(184%2C%20255%2C%20106)` | 11 | 0 | 11 | 0 | 0 |
| `#8a7563` | 10 | 10 | 0 | 0 | 0 |
| `#9ca3af` | 10 | 10 | 0 | 0 | 0 |
| `#e3d6c1` | 10 | 0 | 10 | 0 | 0 |
| `rgb(217%2C%20112%2C%2046)` | 6 | 0 | 6 | 0 | 0 |
| `rgb(239%2C%20144%2C%2067)` | 6 | 0 | 6 | 0 | 0 |
| `#f5ead8` | 6 | 6 | 0 | 0 | 0 |

And 34 more, each on fewer parts.

### Fonts

No faces carried: the site sets words in the Builder's own families.

Faces setting words, by parts:

| Face | Parts | Sizes (px) | Weights |
|---|---|---|---|
| grotesque sans | 316 | 11, 13.3, 16, 17.6, 18.7, 24 | 400, 700 |
| monospace | 76 | 11, 14, 16, 17.6, 18.7, 22, 32 | 400, 700 |

### Radii

The site's corner radius: `6px`.

| Radius | Parts |
|---|---|
| `999px` | 42 |
| `10px` | 23 |
| `18px` | 17 |
| `50px` | 17 |
| `3px` | 9 |
| `6px` | 4 |
| `8px` | 4 |
| `0px 0px 8px 8px` | 2 |
| `28px` | 2 |
| `30px` | 2 |
| `12px` | 1 |
| `14px` | 1 |
| `2px` | 1 |
| `34px` | 1 |
| `48px` | 1 |

### Spacing

The page is drawn at 1440px wide and stretched to the window.

Padding (top right bottom left), most used first:

| Padding | Parts |
|---|---|
| `1px 1px 1px 1px` | 100 |
| `6px 14px 6px 14px` | 41 |
| `1px 6px 1px 6px` | 23 |
| `14px 14px 14px 14px` | 14 |
| `0px 2px 0px 2px` | 10 |
| `4px 12px 4px 12px` | 10 |
| `4px 8px 4px 8px` | 10 |
| `1px 2px 1px 2px` | 8 |
| `8px 8px 8px 8px` | 7 |
| `0px 2px 1px 2px` | 3 |
| `0px 0px 0px 40px` | 2 |
| `2px 4px 2px 4px` | 2 |
| `8px 16px 8px 16px` | 2 |
| `0px 4px 0px 4px` | 1 |
| `0px 70px 0px 70px` | 1 |
| `12px 16px 12px 16px` | 1 |

And 9 more.

## 2. Pages

### Play

- Path: `/`
- File: `index.html`
- Parts: 452, of which 60 sit 4 or fewer levels deep in the captured page and are listed here

| Part id | Kind | Shows | Selector |
|---|---|---|---|
| `n_home_picture_410` | picture | trade-picture | `#n_home_picture_410` |
| `n_home_section_377` | box | tour | `#n_home_section_377` |
| `n_home_section_409` | box | trade-marker | `#n_home_section_409` |
| `n_home_slot_445` | box | tour-highlight | `#n_home_slot_445` |
| `n_home_slot_411` | box | trade-marker-label | `#n_home_slot_411` |
| `n_home_button_138` | cta-primary | Menu | `#n_home_button_138` |
| `n_home_link_4` | prose | Play | `#n_home_link_4` |
| `n_home_section_1` | box | app | `#n_home_section_1` |
| `n_home_section_2` | box | nav | `#n_home_section_2` |
| `n_home_section_3` | box | nav-links | `#n_home_section_3` |
| `n_home_link_5` | prose | Leaderboard | `#n_home_link_5` |
| `n_home_link_6` | prose | My profile | `#n_home_link_6` |
| `n_home_link_7` | prose | How it works | `#n_home_link_7` |
| `n_home_text_139` | prose | Devnet: test SOL only, not real money. | `#n_home_text_139` |
| `n_home_section_8` | box | page-title | `#n_home_section_8` |
| `n_home_text_11` | prose | PonsStars test page | `#n_home_text_11` |
| `n_home_shape_9` | box | page-title-icon | `#n_home_shape_9` |
| `n_home_shape_10` | box | page-title-icon-shape | `#n_home_shape_10` |
| `n_home_text_12` | prose | Test networks only (devnet or a local validator… | `#n_home_text_12` |
| `n_home_section_13` | box | play-layout | `#n_home_section_13` |
| `n_home_section_242` | box | player-card | `#n_home_section_242` |
| `n_home_section_300` | box | profile-panel | `#n_home_section_300` |
| `n_home_section_78` | box | play-side-player | `#n_home_section_78` |
| `n_home_section_79` | box | wallet-panel | `#n_home_section_79` |
| `n_home_text_140` | prose | Game server offline. | `#n_home_text_140` |
| `n_home_section_14` | box | play-center | `#n_home_section_14` |
| `n_home_section_15` | box | next-step | `#n_home_section_15` |
| `n_home_section_94` | box | play-side-money | `#n_home_section_94` |
| `n_home_section_95` | box | balance-panel | `#n_home_section_95` |
| `n_home_section_17` | box | chart-stage | `#n_home_section_17` |
| `n_home_section_378` | box | tour-card | `#n_home_section_378` |
| `n_home_text_379` | prose | - | `#n_home_text_379` |
| `n_home_heading_380` | prose | - | `#n_home_heading_380` |
| `n_home_text_381` | prose | - | `#n_home_text_381` |
| `n_home_section_382` | box | tour-dots | `#n_home_section_382` |
| `n_home_section_393` | box | tour-buttons | `#n_home_section_393` |
| `n_home_text_397` | prose | Keys: left and right arrows to move, Escape to … | `#n_home_text_397` |
| `n_home_section_350` | box | newwallet-panel | `#n_home_section_350` |
| `n_home_section_186` | box | sign-panel | `#n_home_section_186` |
| `n_home_section_58` | box | sign-auto-line | `#n_home_section_58` |
| `n_home_slot_61` | box | sign-status | `#n_home_slot_61` |
| `n_home_section_62` | box | queue-panel | `#n_home_section_62` |
| `n_home_section_122` | box | market-panel | `#n_home_section_122` |
| `n_home_text_349` | prose | Public profile and match history | `#n_home_text_349` |
| `n_home_section_128` | box | connection-panel | `#n_home_section_128` |
| `n_home_section_208` | box | match-panel | `#n_home_section_208` |
| `n_home_section_227` | box | result-panel | `#n_home_section_227` |
| `n_home_section_76` | box | log-panel | `#n_home_section_76` |
| `n_home_button_399` | cta-primary | Connect | `#n_home_button_399` |
| `n_home_section_398` | box | template-wallet-option | `#n_home_section_398` |
| `n_home_section_400` | box | template-queue-stake-option | `#n_home_section_400` |
| `n_home_section_402` | box | template-queue-length-option | `#n_home_section_402` |
| `n_home_section_404` | box | template-queue-chart-option | `#n_home_section_404` |
| `n_home_section_406` | box | template-order-item | `#n_home_section_406` |
| `n_home_section_408` | box | template-trade-marker | `#n_home_section_408` |
| `n_home_shape_412` | box | picture-canvas | `#n_home_shape_412` |
| `n_home_slot_401` | box | queue-stake-option | `#n_home_slot_401` |
| `n_home_slot_403` | box | queue-length-option | `#n_home_slot_403` |
| `n_home_slot_405` | box | queue-chart-option | `#n_home_slot_405` |
| `n_home_slot_407` | box | order-item | `#n_home_slot_407` |

### Profile

- Path: `/profile`
- File: `profile/index.html`
- Parts: 54, of which 42 sit 4 or fewer levels deep in the captured page and are listed here

| Part id | Kind | Shows | Selector |
|---|---|---|---|
| `n_profile_button_17` | cta-primary | Menu | `#n_profile_button_17` |
| `n_profile_link_4` | prose | Play | `#n_profile_link_4` |
| `n_profile_section_1` | box | profile-page | `#n_profile_section_1` |
| `n_profile_section_2` | box | nav | `#n_profile_section_2` |
| `n_profile_section_3` | box | nav-links | `#n_profile_section_3` |
| `n_profile_link_5` | prose | Leaderboard | `#n_profile_link_5` |
| `n_profile_link_6` | prose | How it works | `#n_profile_link_6` |
| `n_profile_section_7` | box | page-title | `#n_profile_section_7` |
| `n_profile_text_10` | prose | Player profile | `#n_profile_text_10` |
| `n_profile_shape_8` | box | page-title-icon | `#n_profile_shape_8` |
| `n_profile_shape_9` | box | page-title-icon-shape | `#n_profile_shape_9` |
| `n_profile_section_11` | box | profile-lookup | `#n_profile_section_11` |
| `n_profile_section_12` | box | profile-lookup-label | `#n_profile_section_12` |
| `n_profile_text_13` | prose | Wallet address | `#n_profile_text_13` |
| `n_profile_text_18` | prose | Game server offline. | `#n_profile_text_18` |
| `n_profile_field_14` | field | profile-lookup-address | `#n_profile_field_14` |
| `n_profile_button_15` | cta-primary | Show | `#n_profile_button_15` |
| `n_profile_picture_53` | picture | profile-card-picture | `#n_profile_picture_53` |
| `n_profile_section_40` | box | template-history-row | `#n_profile_section_40` |
| `n_profile_section_41` | box | history-row | `#n_profile_section_41` |
| `n_profile_slot_16` | box | profile-error | `#n_profile_slot_16` |
| `n_profile_slot_42` | box | history-when | `#n_profile_slot_42` |
| `n_profile_slot_43` | box | history-result | `#n_profile_slot_43` |
| `n_profile_slot_44` | box | history-why | `#n_profile_slot_44` |
| `n_profile_section_45` | box | history-opponent | `#n_profile_section_45` |
| `n_profile_slot_47` | box | history-stake | `#n_profile_slot_47` |
| `n_profile_slot_48` | box | history-best | `#n_profile_slot_48` |
| `n_profile_slot_49` | box | history-profit | `#n_profile_slot_49` |
| `n_profile_slot_50` | box | history-practice | `#n_profile_slot_50` |
| `n_profile_section_51` | box | history-page | `#n_profile_section_51` |
| `n_profile_heading_20` | prose | - | `#n_profile_heading_20` |
| `n_profile_section_19` | box | profile-card | `#n_profile_section_19` |
| `n_profile_text_21` | prose | Wallet: - | `#n_profile_text_21` |
| `n_profile_heading_22` | prose | Practice matches (not counted as real wins) | `#n_profile_heading_22` |
| `n_profile_text_23` | prose | Matches 0, wins 0, losses 0, ties 0, no contest… | `#n_profile_text_23` |
| `n_profile_heading_24` | prose | Live matches only | `#n_profile_heading_24` |
| `n_profile_text_25` | prose | Matches 0, wins 0, losses 0, ties 0, profit and… | `#n_profile_text_25` |
| `n_profile_heading_26` | prose | Match history | `#n_profile_heading_26` |
| `n_profile_section_27` | box | history-table | `#n_profile_section_27` |
| `n_profile_section_28` | box | history-head | `#n_profile_section_28` |
| `n_profile_slot_39` | box | history-rows | `#n_profile_slot_39` |
| `n_profile_text_54` | prose | No finished matches yet. | `#n_profile_text_54` |

### Match result

- Path: `/match`
- File: `match/index.html`
- Parts: 77, of which 55 sit 4 or fewer levels deep in the captured page and are listed here

| Part id | Kind | Shows | Selector |
|---|---|---|---|
| `n_match_button_14` | cta-primary | Menu | `#n_match_button_14` |
| `n_match_link_4` | prose | Play | `#n_match_link_4` |
| `n_match_section_1` | box | match-page | `#n_match_section_1` |
| `n_match_section_2` | box | nav | `#n_match_section_2` |
| `n_match_section_3` | box | nav-links | `#n_match_section_3` |
| `n_match_link_5` | prose | Leaderboard | `#n_match_link_5` |
| `n_match_link_6` | prose | How it works | `#n_match_link_6` |
| `n_match_section_7` | box | page-title | `#n_match_section_7` |
| `n_match_text_10` | prose | Match result | `#n_match_text_10` |
| `n_match_shape_8` | box | page-title-icon | `#n_match_shape_8` |
| `n_match_shape_9` | box | page-title-icon-shape | `#n_match_shape_9` |
| `n_match_text_11` | prose | Anyone can check this result. Your browser reco… | `#n_match_text_11` |
| `n_match_text_15` | prose | Game server offline. | `#n_match_text_15` |
| `n_match_section_16` | box | mr-summary | `#n_match_section_16` |
| `n_match_section_29` | box | template-mr-check | `#n_match_section_29` |
| `n_match_section_64` | box | template-mr-trade-row | `#n_match_section_64` |
| `n_match_section_65` | box | mr-trade-row | `#n_match_section_65` |
| `n_match_slot_12` | box | mr-error | `#n_match_slot_12` |
| `n_match_slot_13` | box | mr-rounds | `#n_match_slot_13` |
| `n_match_slot_30` | box | mr-check | `#n_match_slot_30` |
| `n_match_slot_66` | box | mr-trade-id | `#n_match_slot_66` |
| `n_match_text_17` | prose | Match account: - (id -) | `#n_match_text_17` |
| `n_match_text_76` | prose | Practice match: prices were not live (​). | `#n_match_text_76` |
| `n_match_slot_67` | box | mr-trade-player | `#n_match_slot_67` |
| `n_match_slot_68` | box | mr-trade-side | `#n_match_slot_68` |
| `n_match_slot_69` | box | mr-trade-percent | `#n_match_slot_69` |
| `n_match_slot_70` | box | mr-trade-arrived | `#n_match_slot_70` |
| `n_match_slot_71` | box | mr-trade-status | `#n_match_slot_71` |
| `n_match_slot_72` | box | mr-trade-tick | `#n_match_slot_72` |
| `n_match_slot_73` | box | mr-trade-price | `#n_match_slot_73` |
| `n_match_slot_74` | box | mr-trade-index | `#n_match_slot_74` |
| `n_match_slot_75` | box | mr-trade-sol | `#n_match_slot_75` |
| `n_match_heading_27` | prose | Verification: checking... | `#n_match_heading_27` |
| `n_match_section_26` | box | mr-verify | `#n_match_section_26` |
| `n_match_section_31` | box | template-mr-round | `#n_match_section_31` |
| `n_match_section_32` | box | mr-round | `#n_match_section_32` |
| `n_match_section_34` | box | mr-generated | `#n_match_section_34` |
| `n_match_slot_33` | box | mr-round-title | `#n_match_slot_33` |
| `n_match_text_18` | prose | Player A: -. Player B: -. | `#n_match_text_18` |
| `n_match_slot_28` | box | mr-checks | `#n_match_slot_28` |
| `n_match_text_19` | prose | Stake - SOL each. Length -. | `#n_match_text_19` |
| `n_match_text_20` | prose | - | `#n_match_text_20` |
| `n_match_text_21` | prose | Paid: player A - SOL, player B - SOL, house cut… | `#n_match_text_21` |
| `n_match_section_42` | box | mr-reference | `#n_match_section_42` |
| `n_match_slot_41` | box | mr-round-index | `#n_match_slot_41` |
| `n_match_text_22` | prose | Signed by result key -. This server says its ke… | `#n_match_text_22` |
| `n_match_shape_47` | box | mr-round-chart | `#n_match_shape_47` |
| `n_match_slot_45` | box | mr-round-scores | `#n_match_slot_45` |
| `n_match_slot_46` | box | mr-round-result | `#n_match_slot_46` |
| `n_match_text_23` | prose | Transactions: - | `#n_match_text_23` |
| `n_match_link_25` | prose | Raw record (JSON) | `#n_match_link_25` |
| `n_match_section_24` | box | mr-raw-line | `#n_match_section_24` |
| `n_match_heading_48` | prose | Trade log | `#n_match_heading_48` |
| `n_match_section_49` | box | mr-trades | `#n_match_section_49` |
| `n_match_slot_63` | box | mr-ticks | `#n_match_slot_63` |

### Leaderboard

- Path: `/leaderboard`
- File: `leaderboard/index.html`
- Parts: 43, of which 34 sit 4 or fewer levels deep in the captured page and are listed here

| Part id | Kind | Shows | Selector |
|---|---|---|---|
| `n_leaderboard_button_30` | cta-primary | Menu | `#n_leaderboard_button_30` |
| `n_leaderboard_link_4` | prose | Play | `#n_leaderboard_link_4` |
| `n_leaderboard_section_1` | box | leaderboard-page | `#n_leaderboard_section_1` |
| `n_leaderboard_section_2` | box | nav | `#n_leaderboard_section_2` |
| `n_leaderboard_section_3` | box | nav-links | `#n_leaderboard_section_3` |
| `n_leaderboard_link_5` | prose | Profiles | `#n_leaderboard_link_5` |
| `n_leaderboard_link_6` | prose | How it works | `#n_leaderboard_link_6` |
| `n_leaderboard_section_7` | box | page-title | `#n_leaderboard_section_7` |
| `n_leaderboard_text_10` | prose | Leaderboard | `#n_leaderboard_text_10` |
| `n_leaderboard_shape_8` | box | page-title-icon | `#n_leaderboard_shape_8` |
| `n_leaderboard_shape_9` | box | page-title-icon-shape | `#n_leaderboard_shape_9` |
| `n_leaderboard_section_11` | box | leaderboard-by-label | `#n_leaderboard_section_11` |
| `n_leaderboard_text_12` | prose | Rank by | `#n_leaderboard_text_12` |
| `n_leaderboard_text_31` | prose | Game server offline. | `#n_leaderboard_text_31` |
| `n_leaderboard_section_14` | box | leaderboard-practice-label | `#n_leaderboard_section_14` |
| `n_leaderboard_text_15` | prose | Matches | `#n_leaderboard_text_15` |
| `n_leaderboard_field_13` | field | Wins | `#n_leaderboard_field_13` |
| `n_leaderboard_field_16` | field | Live matches (real wins) | `#n_leaderboard_field_16` |
| `n_leaderboard_section_18` | box | leaderboard-table | `#n_leaderboard_section_18` |
| `n_leaderboard_slot_17` | box | leaderboard-error | `#n_leaderboard_slot_17` |
| `n_leaderboard_section_19` | box | leaderboard-head | `#n_leaderboard_section_19` |
| `n_leaderboard_section_20` | box | leaderboard-head-row | `#n_leaderboard_section_20` |
| `n_leaderboard_slot_29` | box | leaderboard-rows | `#n_leaderboard_slot_29` |
| `n_leaderboard_section_33` | box | template-leaderboard-row | `#n_leaderboard_section_33` |
| `n_leaderboard_section_34` | box | leaderboard-row | `#n_leaderboard_section_34` |
| `n_leaderboard_slot_35` | box | leaderboard-rank | `#n_leaderboard_slot_35` |
| `n_leaderboard_section_36` | box | leaderboard-player | `#n_leaderboard_section_36` |
| `n_leaderboard_slot_38` | box | leaderboard-matches | `#n_leaderboard_slot_38` |
| `n_leaderboard_slot_39` | box | leaderboard-wins | `#n_leaderboard_slot_39` |
| `n_leaderboard_slot_40` | box | leaderboard-losses | `#n_leaderboard_slot_40` |
| `n_leaderboard_slot_41` | box | leaderboard-ties | `#n_leaderboard_slot_41` |
| `n_leaderboard_slot_42` | box | leaderboard-best | `#n_leaderboard_slot_42` |
| `n_leaderboard_slot_43` | box | leaderboard-profit | `#n_leaderboard_slot_43` |
| `n_leaderboard_text_32` | prose | No finished matches yet. | `#n_leaderboard_text_32` |

### Chart library

- Path: `/library`
- File: `library/index.html`
- Parts: 107, of which 83 sit 4 or fewer levels deep in the captured page and are listed here

| Part id | Kind | Shows | Selector |
|---|---|---|---|
| `n_library_button_68` | cta-primary | Menu | `#n_library_button_68` |
| `n_library_link_4` | prose | Play | `#n_library_link_4` |
| `n_library_section_1` | box | library | `#n_library_section_1` |
| `n_library_section_2` | box | nav | `#n_library_section_2` |
| `n_library_section_3` | box | nav-links | `#n_library_section_3` |
| `n_library_link_5` | prose | Leaderboard | `#n_library_link_5` |
| `n_library_section_6` | box | page-title | `#n_library_section_6` |
| `n_library_text_9` | prose | Chart library (owner only) | `#n_library_text_9` |
| `n_library_shape_7` | box | page-title-icon | `#n_library_shape_7` |
| `n_library_shape_8` | box | page-title-icon-shape | `#n_library_shape_8` |
| `n_library_text_10` | prose | Record a coin's pool once a second from the fre… | `#n_library_text_10` |
| `n_library_text_69` | prose | Game server offline. | `#n_library_text_69` |
| `n_library_text_11` | prose | The free game server forgets everything when it… | `#n_library_text_11` |
| `n_library_heading_13` | prose | Admin key | `#n_library_heading_13` |
| `n_library_section_12` | box | lib-key-panel | `#n_library_section_12` |
| `n_library_section_14` | box | lib-key-label | `#n_library_section_14` |
| `n_library_text_15` | prose | Key | `#n_library_text_15` |
| `n_library_field_16` | field | lib-key | `#n_library_field_16` |
| `n_library_button_17` | cta-primary | Use this key | `#n_library_button_17` |
| `n_library_text_18` | prose | Enter the admin key set on the game server (PON… | `#n_library_text_18` |
| `n_library_heading_20` | prose | Record a coin | `#n_library_heading_20` |
| `n_library_section_19` | box | lib-record-panel | `#n_library_section_19` |
| `n_library_section_21` | box | lib-mint-line | `#n_library_section_21` |
| `n_library_section_22` | box | lib-mint-label | `#n_library_section_22` |
| `n_library_text_23` | prose | Token address (mint) | `#n_library_text_23` |
| `n_library_section_25` | box | lib-pool-line | `#n_library_section_25` |
| `n_library_section_26` | box | lib-pool-label | `#n_library_section_26` |
| `n_library_text_27` | prose | Pool address (optional: the coin/SOL pool to fo… | `#n_library_text_27` |
| `n_library_section_29` | box | lib-record-line | `#n_library_section_29` |
| `n_library_section_30` | box | lib-label-label | `#n_library_section_30` |
| `n_library_text_31` | prose | Name for it | `#n_library_text_31` |
| `n_library_section_33` | box | lib-minutes-label | `#n_library_section_33` |
| `n_library_text_34` | prose | Minutes | `#n_library_text_34` |
| `n_library_button_36` | cta-primary | Start recording | `#n_library_button_36` |
| `n_library_slot_37` | box | lib-record-message | `#n_library_slot_37` |
| `n_library_heading_39` | prose | Recordings | `#n_library_heading_39` |
| `n_library_section_38` | box | lib-recordings-panel | `#n_library_section_38` |
| `n_library_section_40` | box | lib-recordings | `#n_library_section_40` |
| `n_library_section_41` | box | lib-recordings-head | `#n_library_section_41` |
| `n_library_slot_48` | box | lib-recordings-rows | `#n_library_slot_48` |
| `n_library_heading_50` | prose | Saved windows | `#n_library_heading_50` |
| `n_library_heading_71` | prose | Pick a window from - | `#n_library_heading_71` |
| `n_library_section_49` | box | lib-windows-panel | `#n_library_section_49` |
| `n_library_section_70` | box | lib-view | `#n_library_section_70` |
| `n_library_section_51` | box | lib-windows | `#n_library_section_51` |
| `n_library_section_72` | box | lib-chart | `#n_library_section_72` |
| `n_library_shape_73` | box | lib-chart-canvas | `#n_library_shape_73` |
| `n_library_section_52` | box | lib-windows-head | `#n_library_section_52` |
| `n_library_slot_60` | box | lib-windows-rows | `#n_library_slot_60` |
| `n_library_button_62` | cta-primary | Export all windows (JSON file) | `#n_library_button_62` |
| `n_library_section_61` | box | lib-file-line | `#n_library_section_61` |
| `n_library_section_63` | box | lib-import-label | `#n_library_section_63` |
| `n_library_text_64` | prose | Import a file | `#n_library_text_64` |
| `n_library_button_66` | cta-primary | Import | `#n_library_button_66` |
| `n_library_section_100` | box | lib-window | `#n_library_section_100` |
| `n_library_section_90` | box | template-lib-recording | `#n_library_section_90` |
| `n_library_section_91` | box | lib-recording | `#n_library_section_91` |
| `n_library_section_99` | box | template-lib-window | `#n_library_section_99` |
| `n_library_slot_101` | box | lib-win-label | `#n_library_slot_101` |
| `n_library_slot_67` | box | lib-file-message | `#n_library_slot_67` |

And 23 more; each is `#<part id>` in `library/index.html`.

### Sample generated chart

- Path: `/chart-lab`
- File: `chart-lab/index.html`
- Parts: 63, of which 39 sit 4 or fewer levels deep in the captured page and are listed here

| Part id | Kind | Shows | Selector |
|---|---|---|---|
| `n_chart-lab_button_63` | cta-primary | Menu | `#n_chart-lab_button_63` |
| `n_chart-lab_link_4` | prose | Play | `#n_chart-lab_link_4` |
| `n_chart-lab_section_1` | box | lab-page | `#n_chart-lab_section_1` |
| `n_chart-lab_section_2` | box | nav | `#n_chart-lab_section_2` |
| `n_chart-lab_section_3` | box | nav-links | `#n_chart-lab_section_3` |
| `n_chart-lab_link_5` | prose | Profiles | `#n_chart-lab_link_5` |
| `n_chart-lab_link_6` | prose | How it works | `#n_chart-lab_link_6` |
| `n_chart-lab_section_7` | box | page-title | `#n_chart-lab_section_7` |
| `n_chart-lab_text_10` | prose | Sample generated chart | `#n_chart-lab_text_10` |
| `n_chart-lab_shape_8` | box | page-title-icon | `#n_chart-lab_shape_8` |
| `n_chart-lab_shape_9` | box | page-title-icon-shape | `#n_chart-lab_shape_9` |
| `n_chart-lab_text_11` | prose | A practice chart made the same way as in a matc… | `#n_chart-lab_text_11` |
| `n_chart-lab_section_12` | box | lab-form | `#n_chart-lab_section_12` |
| `n_chart-lab_section_13` | box | lab-seed-label | `#n_chart-lab_section_13` |
| `n_chart-lab_text_14` | prose | Seed | `#n_chart-lab_text_14` |
| `n_chart-lab_field_15` | field | lab-seed-input | `#n_chart-lab_field_15` |
| `n_chart-lab_section_16` | box | lab-secs-label | `#n_chart-lab_section_16` |
| `n_chart-lab_text_17` | prose | Show | `#n_chart-lab_text_17` |
| `n_chart-lab_section_19` | box | lab-bar-label | `#n_chart-lab_section_19` |
| `n_chart-lab_text_20` | prose | Candles of | `#n_chart-lab_text_20` |
| `n_chart-lab_button_22` | cta-primary | Draw | `#n_chart-lab_button_22` |
| `n_chart-lab_button_23` | cta-primary | New seed | `#n_chart-lab_button_23` |
| `n_chart-lab_field_18` | field | 5 minutes | `#n_chart-lab_field_18` |
| `n_chart-lab_field_21` | field | 1 second | `#n_chart-lab_field_21` |
| `n_chart-lab_shape_24` | box | lab-chart | `#n_chart-lab_shape_24` |
| `n_chart-lab_text_25` | prose | Top: price (100 = start). Bottom: SOL traded ea… | `#n_chart-lab_text_25` |
| `n_chart-lab_heading_26` | prose | Stats over 10,000 seconds of this seed | `#n_chart-lab_heading_26` |
| `n_chart-lab_section_27` | box | lab-stats | `#n_chart-lab_section_27` |
| `n_chart-lab_section_28` | box | lab-stats-head | `#n_chart-lab_section_28` |
| `n_chart-lab_section_29` | box | lab-stats-head-row | `#n_chart-lab_section_29` |
| `n_chart-lab_section_33` | box | lab-stats-body | `#n_chart-lab_section_33` |
| `n_chart-lab_section_34` | box | lab-stat-mean | `#n_chart-lab_section_34` |
| `n_chart-lab_section_38` | box | lab-stat-range | `#n_chart-lab_section_38` |
| `n_chart-lab_section_42` | box | lab-stat-rate | `#n_chart-lab_section_42` |
| `n_chart-lab_section_46` | box | lab-stat-empty | `#n_chart-lab_section_46` |
| `n_chart-lab_section_50` | box | lab-stat-flat | `#n_chart-lab_section_50` |
| `n_chart-lab_section_54` | box | lab-stat-volume | `#n_chart-lab_section_54` |
| `n_chart-lab_section_58` | box | lab-stat-same | `#n_chart-lab_section_58` |
| `n_chart-lab_slot_62` | box | lab-error | `#n_chart-lab_slot_62` |

## 3. Captured behaviour

### Show on press

Pressing the part shows one state of its group and hides the others. The export shows each group's first state; the pressed states are on the board as parts of their own.

Parts belonging to each state:

| Group | State | Parts |
|---|---|---|
| `hidden:balance-faucet` | 1 | 1 |
| `hidden:balance-play-money` | 1 | 1 |
| `hidden:chart-generated` | 1 | 1 |
| `hidden:chart-tv-idle` | 1 | 3 |
| `hidden:chart-tv-idle-button` | 1 | 1 |
| `hidden:chart-tv-match` | 1 | 1 |
| `hidden:chart-tv-result` | 1 | 3 |
| `hidden:deposit-confirm-panel` | 1 | 4 |
| `hidden:duel` | 1 | 4 |
| `hidden:history-empty` | 1 | 1 |
| `hidden:leaderboard-empty` | 1 | 1 |
| `hidden:lib-export-link` | 1 | 1 |
| `hidden:lib-view` | 1 | 19 |
| `hidden:log` | 1 | 1 |
| `hidden:market-practice` | 1 | 1 |
| `hidden:match-panel` | 1 | 19 |
| `hidden:match-practice` | 1 | 1 |
| `hidden:mr-practice` | 1 | 1 |
| `hidden:mr-reference-frame` | 1 | 1 |
| `hidden:mr-summary` | 1 | 10 |
| `hidden:mr-verify` | 1 | 3 |
| `hidden:nav-menu` | 1 | 6 |
| `hidden:network-banner` | 1 | 1 |
| `hidden:newwallet-panel` | 1 | 16 |
| `hidden:newwallet-step-phrase` | 1 | 4 |
| `hidden:newwallet-step-ready` | 1 | 8 |
| `hidden:next-step-button` | 1 | 1 |
| `hidden:no-trade-warning` | 1 | 8 |
| `hidden:opponent-bot` | 1 | 1 |
| `hidden:picture-canvas` | 1 | 1 |
| `hidden:player-card` | 1 | 58 |
| `hidden:profile-card` | 1 | 21 |
| `hidden:profile-card-picture` | 1 | 1 |
| `hidden:profile-panel` | 1 | 50 |
| `hidden:profile-picture-preview` | 1 | 1 |
| `hidden:queue-chart-label` | 1 | 3 |
| `hidden:queue-chart-note` | 1 | 1 |
| `hidden:queue-leave` | 1 | 1 |
| `hidden:reference-frame` | 1 | 1 |
| `hidden:reference-panel` | 1 | 5 |
| `hidden:reference-unavailable` | 1 | 1 |
| `hidden:rematch-panel` | 1 | 5 |
| `hidden:result-coin` | 1 | 3 |
| `hidden:result-generated` | 1 | 5 |
| `hidden:result-panel` | 1 | 14 |
| `hidden:result-practice` | 1 | 1 |
| `hidden:scoreboard` | 1 | 7 |
| `hidden:server-offline` | 1 | 5 |
| `hidden:sign-panel` | 1 | 9 |
| `hidden:start-countdown` | 1 | 1 |
| `hidden:template:template-history-row` | 1 | 13 |
| `hidden:template:template-leaderboard-row` | 1 | 11 |
| `hidden:template:template-lib-recording` | 1 | 9 |
| `hidden:template:template-lib-window` | 1 | 9 |
| `hidden:template:template-mr-check` | 1 | 2 |
| `hidden:template:template-mr-round` | 1 | 33 |
| `hidden:template:template-mr-trade-row` | 1 | 12 |
| `hidden:template:template-order-item` | 1 | 2 |
| `hidden:template:template-queue-chart-option` | 1 | 2 |
| `hidden:template:template-queue-length-option` | 1 | 2 |
| `hidden:template:template-queue-stake-option` | 1 | 2 |
| `hidden:template:template-trade-marker` | 1 | 4 |
| `hidden:template:template-wallet-option` | 1 | 2 |
| `hidden:tour` | 1 | 21 |
| `hidden:tour-highlight` | 1 | 1 |
| `hidden:trade-panel` | 1 | 26 |
| `hidden:withdraw-confirm-panel` | 1 | 4 |

### Motion and hover from the stylesheet

Written into `assets/motion/<page>.css` against each part's box (`.mo-<id>`, or a class the parts moving the same way share); the keyframes are prefixed `cap-` and live in `assets/site.css`. Parts moving the same way are one row.

| Animation | Transition | Hover / press / focus | Parts |
|---|---|---|---|
| — | — | press, focus | 40: `n_home_button_106`, `n_home_button_107`, `n_home_button_113`, `n_home_button_119`, `n_home_button_120`, `n_home_button_141`, `n_home_button_193`, `n_home_button_194`, `n_home_button_199`, `n_home_button_207`, `n_home_button_240`, `n_home_button_325`, and 28 more |
| — | r | — | 2: `n_home_shape_151`, `n_home_shape_152` |
| — | width | — | 1: `n_home_slot_40` |
| pons-tv-antenna-left 3s ease-in-out loops | — | — | 1: `n_home_section_23` |
| pons-tv-antenna-right 3s ease-in-out loops | — | — | 1: `n_home_section_25` |
| pons-tv-blink 1s steps(1) loops | — | — | 1: `n_home_slot_52` |
| pons-tv-static 0.4s steps(1) loops | — | — | 1: `n_home_slot_35` |

## 4. Not captured, for the backend

### Buttons that go nowhere

Nothing happens when these are pressed: no link, and nothing attached.

| Part | Where | Shows |
|---|---|---|
| `n_chart-lab_button_22` | `chart-lab/index.html` `#n_chart-lab_button_22` | Draw |
| `n_chart-lab_button_23` | `chart-lab/index.html` `#n_chart-lab_button_23` | New seed |
| `n_chart-lab_button_63` | `chart-lab/index.html` `#n_chart-lab_button_63` | Menu |
| `n_home_button_106` | `index.html` `#n_home_button_106` | Refresh |
| `n_home_button_107` | `index.html` `#n_home_button_107` | Create balance account |
| `n_home_button_113` | `index.html` `#n_home_button_113` | Review deposit |
| `n_home_button_119` | `index.html` `#n_home_button_119` | All available |
| `n_home_button_120` | `index.html` `#n_home_button_120` | Review withdrawal |
| `n_home_button_138` | `index.html` `#n_home_button_138` | Menu |
| `n_home_button_141` | `index.html` `#n_home_button_141` | - |
| `n_home_button_169` | `index.html` `#n_home_button_169` | 10% |
| `n_home_button_170` | `index.html` `#n_home_button_170` | 25% |
| `n_home_button_171` | `index.html` `#n_home_button_171` | 50% |
| `n_home_button_172` | `index.html` `#n_home_button_172` | 100% |
| `n_home_button_180` | `index.html` `#n_home_button_180` | 10% |
| `n_home_button_181` | `index.html` `#n_home_button_181` | 25% |
| `n_home_button_182` | `index.html` `#n_home_button_182` | 50% |
| `n_home_button_183` | `index.html` `#n_home_button_183` | 100% |
| `n_home_button_193` | `index.html` `#n_home_button_193` | Approve |
| `n_home_button_194` | `index.html` `#n_home_button_194` | Decline |
| `n_home_button_199` | `index.html` `#n_home_button_199` | Leave queue |
| `n_home_button_206` | `index.html` `#n_home_button_206` | Queue |
| `n_home_button_207` | `index.html` `#n_home_button_207` | Cancel |
| `n_home_button_240` | `index.html` `#n_home_button_240` | Back to queue |
| `n_home_button_325` | `index.html` `#n_home_button_325` | Remove picture |
| `n_home_button_328` | `index.html` `#n_home_button_328` | profile-avatar-sun |
| `n_home_button_330` | `index.html` `#n_home_button_330` | profile-avatar-moon |
| `n_home_button_332` | `index.html` `#n_home_button_332` | profile-avatar-star |
| `n_home_button_334` | `index.html` `#n_home_button_334` | profile-avatar-bolt |
| `n_home_button_336` | `index.html` `#n_home_button_336` | profile-avatar-leaf |
| `n_home_button_338` | `index.html` `#n_home_button_338` | profile-avatar-wave |
| `n_home_button_340` | `index.html` `#n_home_button_340` | profile-avatar-gem |
| `n_home_button_342` | `index.html` `#n_home_button_342` | profile-avatar-rocket |
| `n_home_button_345` | `index.html` `#n_home_button_345` | Use the avatar made from my wallet address |
| `n_home_button_346` | `index.html` `#n_home_button_346` | Save profile |
| `n_home_button_359` | `index.html` `#n_home_button_359` | Create the wallet |
| `n_home_button_360` | `index.html` `#n_home_button_360` | Cancel |
| `n_home_button_364` | `index.html` `#n_home_button_364` | Use this phrase |
| `n_home_button_367` | `index.html` `#n_home_button_367` | Get 3 test SOL in the wallet (test networks onl… |
| `n_home_button_370` | `index.html` `#n_home_button_370` | Confirm deposit |
| `n_home_button_371` | `index.html` `#n_home_button_371` | Cancel |
| `n_home_button_374` | `index.html` `#n_home_button_374` | Confirm withdrawal |
| `n_home_button_375` | `index.html` `#n_home_button_375` | Cancel |
| `n_home_button_383` | `index.html` `#n_home_button_383` | • |
| `n_home_button_384` | `index.html` `#n_home_button_384` | • |
| `n_home_button_385` | `index.html` `#n_home_button_385` | • |
| `n_home_button_386` | `index.html` `#n_home_button_386` | • |
| `n_home_button_387` | `index.html` `#n_home_button_387` | • |
| `n_home_button_388` | `index.html` `#n_home_button_388` | • |
| `n_home_button_389` | `index.html` `#n_home_button_389` | • |
| `n_home_button_390` | `index.html` `#n_home_button_390` | • |
| `n_home_button_391` | `index.html` `#n_home_button_391` | • |
| `n_home_button_392` | `index.html` `#n_home_button_392` | • |
| `n_home_button_394` | `index.html` `#n_home_button_394` | Back |
| `n_home_button_395` | `index.html` `#n_home_button_395` | Skip |
| `n_home_button_396` | `index.html` `#n_home_button_396` | Next |
| `n_home_button_399` | `index.html` `#n_home_button_399` | Connect |
| `n_home_button_413` | `index.html` `#n_home_button_413` | - |
| `n_home_button_429` | `index.html` `#n_home_button_429` | Accept rematch |
| `n_home_button_430` | `index.html` `#n_home_button_430` | Decline (both refunded minus the cut) |
| `n_home_button_436` | `index.html` `#n_home_button_436` | I have written it down. Hide it. |
| `n_home_button_443` | `index.html` `#n_home_button_443` | Send from my connected wallet |
| `n_home_button_444` | `index.html` `#n_home_button_444` | Switch to the new wallet |
| `n_home_button_74` | `index.html` `#n_home_button_74` | Find a match |
| `n_home_button_87` | `index.html` `#n_home_button_87` | Use test wallet (made in this browser) |
| `n_home_button_88` | `index.html` `#n_home_button_88` | Forget test wallet |
| `n_home_button_89` | `index.html` `#n_home_button_89` | Create a new wallet for PonsStars |
| `n_home_button_90` | `index.html` `#n_home_button_90` | Disconnect |
| `n_leaderboard_button_30` | `leaderboard/index.html` `#n_leaderboard_button_30` | Menu |
| `n_library_button_107` | `library/index.html` `#n_library_button_107` | Delete |
| `n_library_button_17` | `library/index.html` `#n_library_button_17` | Use this key |
| `n_library_button_36` | `library/index.html` `#n_library_button_36` | Start recording |
| `n_library_button_62` | `library/index.html` `#n_library_button_62` | Export all windows (JSON file) |
| `n_library_button_66` | `library/index.html` `#n_library_button_66` | Import |
| `n_library_button_68` | `library/index.html` `#n_library_button_68` | Menu |
| `n_library_button_87` | `library/index.html` `#n_library_button_87` | Save this window |
| `n_library_button_97` | `library/index.html` `#n_library_button_97` | Pick windows |
| `n_library_button_98` | `library/index.html` `#n_library_button_98` | Stop |
| `n_match_button_14` | `match/index.html` `#n_match_button_14` | Menu |
| `n_match_button_39` | `match/index.html` `#n_match_button_39` | Verify: regenerate the chart from the seed |
| `n_match_button_44` | `match/index.html` `#n_match_button_44` | Show the DexScreener reference chart |
| `n_profile_button_15` | `profile/index.html` `#n_profile_button_15` | Show |
| `n_profile_button_17` | `profile/index.html` `#n_profile_button_17` | Menu |

## 5. Source

- Repository: `sparkygogo77-spec/PST`
- Branch: `claude/wizardly-davinci-92ah39`
- Commit: not recorded
