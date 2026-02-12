# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trump304 is an electronic implementation of the **304 card game** (popular in Sri Lanka) designed for 2-4 online players. The project is currently in the **rules specification phase** — no application code has been written yet. The game rules are fully documented in `game_rules.txt`.

## Repository Structure

- `game_rules.txt` — Complete game rules specification (the authoritative reference for all game logic)

## Key Game Concepts (for implementation)

- **Deck:** 32 cards (7-A in all suits, no 2-6), totaling 304 points (hence the name)
- **Card hierarchy (by points):** J(30) > 9(20) > A(11) > 10(10) > K(3) > Q(2) > 8(0) > 7(0)
- **Player modes:** 2-player (with center draw pile), 3-player (1 vs 2, dynamic teams), 4-player (2v2 fixed teams)
- **Core flow:** Deal → Bid → Trump selection (hidden) → 8 tricks → Score
- **Trump mechanic:** Chosen secretly by highest bidder, placed face-down, revealed only when cutting is requested or trumper chooses to reveal
- **Bidding:** Minimum 150, multiples of 10; bids of 200+ unlock special rules (re-bidding, overbidding partner)
- **Scoring tiers:** 150-190 (5/3 pts), 200-300 (6/5 pts), 304 (10/7 pts) — trumper win/lose
- **Spoilt trump:** If all 8 trump cards end up with trumper's team, game is void
- **Turn timeout:** 30 seconds per turn; system auto-plays a random valid card on timeout

## Implementation Notes

When building game logic, always validate against `game_rules.txt` — it contains edge cases for cutting, trump revelation timing, 3-player card exchange, rule violations (opposing team wins game + 2 bonus tokens), and communication restrictions.
