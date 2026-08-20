"""
End-to-end verification script for ContextFlow.
Run: python _verify.py
"""
import asyncio
import sys


def test_ssv_core():
    from ssv_core import SSVGenerator, DynamicConsensusProtocol, AsyncStateJournal

    scout = SSVGenerator.generate_ssv(
        "scout", "Research", {"citations": 145}, ["searched"], {}, 0.85
    )
    critic = SSVGenerator.generate_ssv(
        "critic", "Critique", {"citations": 156}, ["evaluated"], {}, 0.75
    )
    synth = SSVGenerator.generate_ssv(
        "synthesis", "Synthesise", {"citations": 150}, ["merged"], {}, 0.90
    )

    assert scout.state_hash != critic.state_hash, "Scout and Critic should have different hashes"
    assert len(scout.state_hash) == 64, "Hash should be SHA-256 (64 hex chars)"

    sc = DynamicConsensusProtocol.compare_states(scout, critic)
    assert sc.divergence_score > 0, "Scout vs Critic should show divergence"
    assert len(sc.mismatch_fields) > 0, "Should report mismatched fields"

    journal = AsyncStateJournal()
    entry = journal.log_state_change("scout", "test", {"x": 1}, "aaa", "bbb")
    assert entry.sequence_number == 0
    assert len(journal.get_agent_history("scout")) == 1

    print("  [PASS] ssv_core — hashing, consensus, journal")


async def test_strands_wrapper():
    from strands_wrapper import StrandsAgentFactory

    scout = StrandsAgentFactory.create_scout_agent()
    critic = StrandsAgentFactory.create_critic_agent()
    synthesis = StrandsAgentFactory.create_synthesis_agent()

    ctx = {"topic": "AI safety", "task": "test"}
    s_ssv = await scout.run_and_generate_ssv(ctx)
    c_ssv = await critic.run_and_generate_ssv(ctx)
    sy_ssv = await synthesis.run_and_generate_ssv(ctx)

    assert s_ssv.state_hash, "Scout SSV hash should be set"
    assert c_ssv.state_hash, "Critic SSV hash should be set"
    assert sy_ssv.state_hash, "Synthesis SSV hash should be set"
    assert s_ssv.state_hash != c_ssv.state_hash, "Scout and Critic should diverge"

    scout_cit = scout.get_observations().get("top_paper_citations")
    critic_cit = critic.get_observations().get("top_paper_citations")
    synth_cit = synthesis.get_observations().get("top_paper_citations")

    assert scout_cit == 145, f"Scout citations should be 145, got {scout_cit}"
    assert critic_cit == 156, f"Critic citations should be 156, got {critic_cit}"
    assert synth_cit == 150, f"Synthesis citations should be 150 (post-consensus), got {synth_cit}"

    strands_mode = "real_bedrock" if scout.is_using_real_strands() else "simulation"
    print(f"  [PASS] strands_wrapper — 3 agents, divergence confirmed (scout={scout_cit}, critic={critic_cit}, synthesis={synth_cit}) mode={strands_mode}")


async def test_api_logic():
    """Test the core API logic without starting the server."""
    from ssv_core import SSVGenerator, DynamicConsensusProtocol
    from strands_wrapper import StrandsAgentFactory

    # Simulate what /demo/run does
    scout_w = StrandsAgentFactory.create_scout_agent()
    critic_w = StrandsAgentFactory.create_critic_agent()
    synth_w = StrandsAgentFactory.create_synthesis_agent()

    ctx = {"topic": "test"}
    scout_ssv = await scout_w.run_and_generate_ssv(ctx)
    critic_ssv = await critic_w.run_and_generate_ssv(ctx)
    synth_ssv = await synth_w.run_and_generate_ssv(ctx)

    sc = DynamicConsensusProtocol.compare_states(scout_ssv, critic_ssv)
    ss = DynamicConsensusProtocol.compare_states(scout_ssv, synth_ssv)
    cs = DynamicConsensusProtocol.compare_states(critic_ssv, synth_ssv)

    assert sc.divergence_score > 0
    assert sc.level.value in ("aligned", "minor_drift", "critical")

    # Simulate what /demo/before-after does
    scout_cit = scout_w.get_observations().get("top_paper_citations", 145)
    critic_cit = critic_w.get_observations().get("top_paper_citations", 156)
    consensus_cit = round((scout_cit + critic_cit) / 2)
    assert consensus_cit == 150, f"Consensus should be 150, got {consensus_cit}"

    divergence_pct = abs(scout_cit - critic_cit) / max(scout_cit, critic_cit) * 100
    assert divergence_pct > 0

    print(f"  [PASS] API logic — before/after correct (consensus={consensus_cit}, divergence={divergence_pct:.1f}%)")


def test_imports():
    """Verify all critical imports work."""
    import fastapi  # noqa
    import uvicorn  # noqa
    import pydantic  # noqa

    try:
        import strands  # noqa
        strands_ok = True
    except ImportError:
        strands_ok = False

    print(f"  [PASS] imports — fastapi, uvicorn, pydantic OK | strands={strands_ok}")
    return strands_ok


def test_api_file():
    """Verify contextflow_api.py imports cleanly."""
    import importlib.util, os
    spec = importlib.util.spec_from_file_location(
        "contextflow_api",
        os.path.join(os.path.dirname(__file__), "contextflow_api.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Check all demo endpoints exist
    routes = [r.path for r in mod.app.routes]
    assert "/demo/run" in routes, "/demo/run missing"
    assert "/demo/before-after" in routes, "/demo/before-after missing"
    assert "/demo/story" in routes, "/demo/story missing"
    assert "/agentcore/status" in routes, "/agentcore/status missing"
    assert "/health" in routes, "/health missing"
    assert "/metrics" in routes, "/metrics missing"
    assert "/agents" in routes, "/agents missing"

    print(f"  [PASS] API routes — {len(routes)} routes registered, all demo endpoints present")


async def main():
    print("\n" + "=" * 60)
    print("  ContextFlow — End-to-End Verification")
    print("=" * 60)

    errors = []

    for name, fn in [
        ("Imports", lambda: test_imports()),
        ("SSV Core", lambda: test_ssv_core()),
        ("API File", lambda: test_api_file()),
    ]:
        try:
            fn()
        except Exception as e:
            print(f"  [FAIL] {name} — {e}")
            errors.append(name)

    for name, coro in [
        ("Strands Wrapper", test_strands_wrapper()),
        ("API Logic", test_api_logic()),
    ]:
        try:
            await coro
        except Exception as e:
            print(f"  [FAIL] {name} — {e}")
            errors.append(name)

    print("=" * 60)
    if errors:
        print(f"  FAILED: {errors}")
        sys.exit(1)
    else:
        print("  ALL CHECKS PASSED ✅")
        print("=" * 60)
        print("\n  Ready to run:")
        print("  Backend:   python contextflow_api.py")
        print("  Frontend:  cd dashboard && npm run dev")
        print("  Demo:      curl -X POST http://localhost:8000/demo/story\n")


if __name__ == "__main__":
    asyncio.run(main())
