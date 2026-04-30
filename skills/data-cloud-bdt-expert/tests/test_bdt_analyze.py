"""Unit tests for bdt_analyze.py.

Run:
    cd afv-library/skills/data-cloud-bdt-expert
    python -m unittest tests.test_bdt_analyze -v
"""
import argparse
import contextlib
import io
import json
import pathlib
import sys
import unittest

# Add scripts/ to path so we can import the module
SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

import bdt_analyze  # noqa: E402


class TestLoad(unittest.TestCase):
    """Loading a valid BDT JSON."""

    def test_load_minimal(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        self.assertEqual(bdt.version, "66.0")
        self.assertEqual(len(bdt.nodes), 3)
        self.assertIn("LOAD_DATASET0", bdt.nodes)
        self.assertIn("FORMULA0", bdt.nodes)
        self.assertIn("OUTPUT0", bdt.nodes)


class TestBadInput(unittest.TestCase):
    """Adversarial / malformed inputs. Raise BdtInputError."""

    def test_invalid_json_raises(self):
        p = FIXTURES / "_tmp_invalid.json"
        self.addCleanup(p.unlink, missing_ok=True)
        p.write_text("{not valid json")
        with self.assertRaises(bdt_analyze.BdtInputError) as cm:
            bdt_analyze.DataTransform.from_path(p)
        self.assertIn("Invalid JSON", str(cm.exception))

    def test_missing_nodes_raises(self):
        with self.assertRaises(bdt_analyze.BdtInputError):
            bdt_analyze.DataTransform.from_dict({"version": "66.0"})

    def test_nodes_not_object_raises(self):
        with self.assertRaises(bdt_analyze.BdtInputError):
            bdt_analyze.DataTransform.from_dict({"nodes": "not-an-object"})

    def test_node_missing_action_raises(self):
        with self.assertRaises(bdt_analyze.BdtInputError) as cm:
            bdt_analyze.DataTransform.from_dict({
                "nodes": {"X": {"sources": []}}
            })
        self.assertIn("missing string 'action'", str(cm.exception))

    def test_node_sources_not_list_raises(self):
        with self.assertRaises(bdt_analyze.BdtInputError):
            bdt_analyze.DataTransform.from_dict({
                "nodes": {"X": {"action": "load", "sources": "not-a-list"}}
            })

    def test_nonexistent_file_raises(self):
        with self.assertRaises(bdt_analyze.BdtInputError):
            bdt_analyze.DataTransform.from_path(FIXTURES / "_does_not_exist.json")


class TestEmptyNodes(unittest.TestCase):
    """`nodes: {}` is valid — no graph, but don't crash."""

    def test_empty_nodes_parses(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "empty_nodes.json")
        self.assertEqual(bdt.nodes, {})


class TestGraph(unittest.TestCase):
    """Graph primitives — roots, sinks, topo order."""

    def setUp(self):
        self.bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")

    def test_roots(self):
        roots = self.bdt.roots()
        self.assertEqual(roots, ["LOAD_DATASET0"])

    def test_sinks(self):
        sinks = self.bdt.sinks()
        self.assertEqual(sinks, ["OUTPUT0"])

    def test_topo_order(self):
        order = self.bdt.topo_order()
        self.assertEqual(order, ["LOAD_DATASET0", "FORMULA0", "OUTPUT0"])

    def test_topo_order_is_valid(self):
        """Every node appears after all its sources."""
        order = self.bdt.topo_order()
        position = {name: i for i, name in enumerate(order)}
        for n in self.bdt.nodes.values():
            for s in n.sources:
                self.assertLess(position[s], position[n.name],
                                f"{s} should come before {n.name}")


class TestCycle(unittest.TestCase):
    """Cycle detection surfaces a clear error."""

    def test_cycle_raises(self):
        with self.assertRaises(bdt_analyze.BdtInputError) as cm:
            bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "cycle.json")
            bdt.topo_order()
        msg = str(cm.exception)
        self.assertIn("Cycle", msg)
        # All three nodes are stuck
        self.assertIn("'A'", msg)
        self.assertIn("'B'", msg)
        self.assertIn("'C'", msg)


class TestTraversal(unittest.TestCase):
    def setUp(self):
        self.bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")

    def test_upstream_of_output(self):
        # OUTPUT0 ← FORMULA0 ← LOAD_DATASET0
        up = self.bdt.upstream("OUTPUT0")
        self.assertEqual(up, ["LOAD_DATASET0", "FORMULA0"])  # topo order

    def test_upstream_of_root_is_empty(self):
        self.assertEqual(self.bdt.upstream("LOAD_DATASET0"), [])

    def test_upstream_unknown_node_raises(self):
        with self.assertRaises(bdt_analyze.BdtNotFoundError):
            self.bdt.upstream("NO_SUCH_NODE")

    def test_downstream_of_root(self):
        # LOAD_DATASET0 → FORMULA0 → OUTPUT0
        down = self.bdt.downstream("LOAD_DATASET0")
        self.assertEqual(down, ["FORMULA0", "OUTPUT0"])

    def test_downstream_of_sink_is_empty(self):
        self.assertEqual(self.bdt.downstream("OUTPUT0"), [])


class TestBrokenReferences(unittest.TestCase):
    def test_broken_references_reported(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "broken_ref.json")
        broken = bdt.broken_references()
        # One entry: (referring_node, missing_source)
        self.assertEqual(broken, [("JOIN0", "NO_SUCH_NODE")])

    def test_no_broken_references_on_clean_bdt(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        self.assertEqual(bdt.broken_references(), [])

    def test_topo_raises_on_broken_ref(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "broken_ref.json")
        with self.assertRaises(bdt_analyze.BdtInputError):
            bdt.topo_order()


class TestResilience(unittest.TestCase):
    """Skill must never crash on schema evolution or missing ui section."""

    def test_unknown_action_loads_without_crash(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "unknown_action.json")
        self.assertEqual(bdt.nodes["MYSTERY0"].action, "someFutureAction")
        # Parameters preserved verbatim
        self.assertEqual(bdt.nodes["MYSTERY0"].parameters, {"foo": "bar"})
        # Graph operations still work
        self.assertEqual(bdt.topo_order(), ["LOAD0", "MYSTERY0"])

    def test_no_ui_section_loads_without_crash(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "no_ui.json")
        # display_name falls back to node key when no ui label
        self.assertEqual(bdt.nodes["LOAD0"].display_name, "LOAD0")

    def test_display_name_uses_label_when_present(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        self.assertEqual(bdt.nodes["LOAD_DATASET0"].display_name, "Account (LOAD_DATASET0)")


class TestSummary(unittest.TestCase):
    def test_summary_markdown_has_key_sections(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False)
        out = bdt_analyze.cmd_summary(bdt, args)
        # Top-line shape
        self.assertIn("# BDT Summary", out)
        self.assertIn("Version: 66.0", out)
        self.assertIn("Total nodes: 3", out)
        # Action counts
        self.assertIn("load: 1", out)
        self.assertIn("formula: 1", out)
        self.assertIn("outputD360: 1", out)
        # Sources table includes the load's dataset
        self.assertIn("ssot__Account__dlm", out)
        # Outputs table includes the output's target
        self.assertIn("Account_Upper__dlm", out)

    def test_summary_json_mode(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=True)
        out = bdt_analyze.cmd_summary(bdt, args)
        parsed = json.loads(out)  # must be valid JSON
        self.assertEqual(parsed["version"], "66.0")
        self.assertEqual(parsed["total_nodes"], 3)
        self.assertEqual(parsed["action_counts"]["load"], 1)

    def test_summary_empty_nodes(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "empty_nodes.json")
        args = argparse.Namespace(as_json=False)
        out = bdt_analyze.cmd_summary(bdt, args)
        self.assertIn("Total nodes: 0", out)


class TestSources(unittest.TestCase):
    def test_sources_markdown(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False)
        out = bdt_analyze.cmd_sources(bdt, args)
        self.assertIn("# Sources", out)
        self.assertIn("LOAD_DATASET0", out)
        self.assertIn("ssot__Account__dlm", out)
        # Fields are listed
        self.assertIn("ssot__Id__c", out)
        self.assertIn("ssot__Name__c", out)

    def test_sources_json(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=True)
        out = bdt_analyze.cmd_sources(bdt, args)
        data = json.loads(out)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "LOAD_DATASET0")
        self.assertIn("ssot__Id__c", data[0]["fields"])


class TestOutputs(unittest.TestCase):
    def test_outputs_markdown(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False)
        out = bdt_analyze.cmd_outputs(bdt, args)
        self.assertIn("# Outputs", out)
        self.assertIn("OUTPUT0", out)
        self.assertIn("Account_Upper__dlm", out)
        self.assertIn("OVERWRITE", out)
        # Mapping table
        self.assertIn("ssot__Id__c", out)
        self.assertIn("Name_Upper__c", out)

    def test_outputs_json(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=True)
        data = json.loads(bdt_analyze.cmd_outputs(bdt, args))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["target_name"], "Account_Upper__dlm")
        self.assertEqual(data[0]["write_mode"], "OVERWRITE")


class TestStages(unittest.TestCase):
    def test_stages_follows_topo_order(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False)
        out = bdt_analyze.cmd_stages(bdt, args)
        self.assertIn("# Stages", out)
        # Ordering: LOAD_DATASET0 must come before FORMULA0 which must come before OUTPUT0
        i_load = out.index("LOAD_DATASET0")
        i_formula = out.index("FORMULA0")
        i_output = out.index("OUTPUT0")
        self.assertLess(i_load, i_formula)
        self.assertLess(i_formula, i_output)
        # Hints present
        self.assertIn("load", out.lower())
        self.assertIn("formula", out.lower())
        self.assertIn("outputD360", out)

    def test_stages_json(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=True)
        data = json.loads(bdt_analyze.cmd_stages(bdt, args))
        self.assertEqual([n["name"] for n in data],
                         ["LOAD_DATASET0", "FORMULA0", "OUTPUT0"])


class TestNodes(unittest.TestCase):
    def test_nodes_table_present(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False, limit=0)
        out = bdt_analyze.cmd_nodes(bdt, args)
        self.assertIn("| Node |", out)
        self.assertIn("LOAD_DATASET0", out)
        self.assertIn("FORMULA0", out)
        self.assertIn("OUTPUT0", out)

    def test_nodes_limit(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False, limit=1)
        out = bdt_analyze.cmd_nodes(bdt, args)
        # Only the first node appears (LOAD_DATASET0 in topo order)
        self.assertIn("LOAD_DATASET0", out)
        self.assertNotIn("OUTPUT0", out)
        self.assertIn("limited to 1", out.lower())


class TestNodeDetail(unittest.TestCase):
    def test_node_detail_markdown(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False, node_name="FORMULA0")
        out = bdt_analyze.cmd_node(bdt, args)
        self.assertIn("# FORMULA0", out)
        self.assertIn("formula", out)
        self.assertIn("upper(ssot__Name__c)", out)
        # Sources and consumers listed
        self.assertIn("LOAD_DATASET0", out)
        self.assertIn("OUTPUT0", out)

    def test_node_detail_unknown_raises_not_found(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False, node_name="NOPE")
        with self.assertRaises(bdt_analyze.BdtNotFoundError):
            bdt_analyze.cmd_node(bdt, args)

    def test_node_cli_unknown_exits_2(self):
        """End-to-end: `bdt_analyze.py node <path> NOPE` exits 2."""
        test = TestCliDispatch()
        code, out, err = test._run(["node", str(FIXTURES / "minimal.json"), "NOPE"])
        self.assertEqual(code, 2)
        self.assertIn("No node named", err)


class TestCliDispatch(unittest.TestCase):
    """Top-level CLI: argparse routing + exit codes."""

    def _run(self, argv):
        """Run bdt_analyze.main with argv and capture (exit_code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        code = None
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = bdt_analyze.main(argv)
        except SystemExit as e:
            code = e.code
        return code, out.getvalue(), err.getvalue()

    def test_no_args_prints_help_exit_2(self):
        code, out, err = self._run([])
        # argparse exits 2 when no subcommand is given
        self.assertEqual(code, 2)
        self.assertIn("usage:", (out + err).lower())

    def test_unknown_subcommand_exit_2(self):
        code, out, err = self._run(["nonexistent", str(FIXTURES / "minimal.json")])
        self.assertEqual(code, 2)

    def test_missing_file_exit_3(self):
        code, out, err = self._run(["summary", str(FIXTURES / "_does_not_exist.json")])
        self.assertEqual(code, 3)
        self.assertIn("cannot read", err.lower())


class TestOutputSizeBudget(unittest.TestCase):
    """Outputs must stay within the 5 KB per-subcommand budget on a tiny BDT."""

    SIZE_LIMIT = 5 * 1024  # 5 KB — per spec §3

    def _run(self, argv):
        test = TestCliDispatch()
        return test._run(argv)

    def test_summary_size(self):
        code, out, err = self._run(["summary", str(FIXTURES / "minimal.json")])
        self.assertEqual(code, 0)
        self.assertLess(len(out), self.SIZE_LIMIT)

    def test_stages_size(self):
        code, out, err = self._run(["stages", str(FIXTURES / "minimal.json")])
        self.assertEqual(code, 0)
        self.assertLess(len(out), self.SIZE_LIMIT)

    def test_nodes_size(self):
        code, out, err = self._run(["nodes", str(FIXTURES / "minimal.json")])
        self.assertEqual(code, 0)
        self.assertLess(len(out), self.SIZE_LIMIT)

    def test_node_detail_size(self):
        code, out, err = self._run(["node", str(FIXTURES / "minimal.json"), "FORMULA0"])
        self.assertEqual(code, 0)
        self.assertLess(len(out), 2 * 1024)  # node detail target: ≤ 2 KB

    def test_lineage_size(self):
        test = TestCliDispatch()
        code, out, err = test._run(["lineage", str(FIXTURES / "minimal.json"), "OUTPUT0"])
        self.assertEqual(code, 0)
        self.assertLess(len(out), 2 * 1024)  # L1 target: ≤ 2 KB

    def test_field_trace_size(self):
        test = TestCliDispatch()
        code, out, err = test._run(["field-trace", str(FIXTURES / "minimal.json"),
                                    "AccountNameUpper__c"])
        self.assertEqual(code, 0)
        self.assertLess(len(out), 1 * 1024)  # L3 target: ≤ 1 KB

    def test_formula_size(self):
        test = TestCliDispatch()
        code, out, err = test._run(["formula", str(FIXTURES / "minimal.json"), "FORMULA0"])
        self.assertEqual(code, 0)
        self.assertLess(len(out), 1 * 1024)  # I1 target: ≤ 1 KB


class TestTraversalResilience(unittest.TestCase):
    """Upstream/downstream must not crash on BDTs with broken refs or cycles,
    as long as the queried node's own walk is well-formed."""

    def test_upstream_works_with_unrelated_broken_ref(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "broken_ref.json")
        # JOIN0's second source NO_SUCH_NODE is broken; LOAD0 is clean.
        # upstream('JOIN0') should return the clean ancestors, not crash.
        up = bdt.upstream("JOIN0")
        self.assertIn("LOAD0", up)

    def test_downstream_works_when_unrelated_nodes_have_broken_refs(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "broken_ref.json")
        down = bdt.downstream("LOAD0")
        self.assertIn("JOIN0", down)

    def test_broken_references_is_sorted(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "adversarial" / "broken_ref.json")
        broken = bdt.broken_references()
        self.assertEqual(broken, sorted(broken))

    def test_from_path_on_directory_raises_input_error(self):
        """OSError subclasses (IsADirectoryError) should be mapped to BdtInputError."""
        import pathlib
        with self.assertRaises(bdt_analyze.BdtInputError) as cm:
            bdt_analyze.DataTransform.from_path(FIXTURES)  # the fixtures dir itself
        self.assertIn("Cannot read", str(cm.exception))


class TestLineage(unittest.TestCase):
    def setUp(self):
        self.bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")

    def test_lineage_of_output_markdown(self):
        args = argparse.Namespace(as_json=False, node_name="OUTPUT0")
        out = bdt_analyze.cmd_lineage(self.bdt, args)
        self.assertIn("# Lineage of OUTPUT0", out)
        # Both upstream nodes named, in topo order
        i_load = out.index("LOAD_DATASET0")
        i_formula = out.index("FORMULA0")
        self.assertLess(i_load, i_formula)

    def test_lineage_of_root_says_root(self):
        args = argparse.Namespace(as_json=False, node_name="LOAD_DATASET0")
        out = bdt_analyze.cmd_lineage(self.bdt, args)
        self.assertIn("is a graph root", out)

    def test_lineage_unknown_raises(self):
        args = argparse.Namespace(as_json=False, node_name="NOPE")
        with self.assertRaises(bdt_analyze.BdtNotFoundError):
            bdt_analyze.cmd_lineage(self.bdt, args)

    def test_lineage_json(self):
        args = argparse.Namespace(as_json=True, node_name="OUTPUT0")
        data = json.loads(bdt_analyze.cmd_lineage(self.bdt, args))
        self.assertEqual(data["target"], "OUTPUT0")
        self.assertEqual(data["upstream"],
                         [{"name": "LOAD_DATASET0", "action": "load",
                           "label": "Account", "sources": []},
                          {"name": "FORMULA0", "action": "formula",
                           "label": "Uppercase Name", "sources": ["LOAD_DATASET0"]}])


class TestFieldDiscovery(unittest.TestCase):
    def setUp(self):
        self.bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")

    def test_load_produces_its_field_list(self):
        n = self.bdt.nodes["LOAD_DATASET0"]
        produced = bdt_analyze.fields_produced(n)
        self.assertIn("ssot__Id__c", produced)
        self.assertIn("ssot__Name__c", produced)

    def test_load_consumes_nothing(self):
        n = self.bdt.nodes["LOAD_DATASET0"]
        self.assertEqual(bdt_analyze.fields_consumed(n), [])

    def test_formula_produces_its_output_field(self):
        n = self.bdt.nodes["FORMULA0"]
        produced = bdt_analyze.fields_produced(n)
        self.assertEqual(produced, ["AccountNameUpper__c"])

    def test_formula_consumes_fields_mentioned_in_expression(self):
        n = self.bdt.nodes["FORMULA0"]
        consumed = bdt_analyze.fields_consumed(n)
        self.assertIn("ssot__Name__c", consumed)

    def test_output_consumes_source_fields_from_mappings(self):
        n = self.bdt.nodes["OUTPUT0"]
        consumed = bdt_analyze.fields_consumed(n)
        self.assertIn("ssot__Id__c", consumed)
        self.assertIn("AccountNameUpper__c", consumed)

    def test_output_produces_target_fields_from_mappings(self):
        n = self.bdt.nodes["OUTPUT0"]
        produced = bdt_analyze.fields_produced(n)
        self.assertIn("ssot__Id__c", produced)
        self.assertIn("Name_Upper__c", produced)


class TestFieldTrace(unittest.TestCase):
    def setUp(self):
        self.bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")

    def test_trace_field_defined_in_formula(self):
        args = argparse.Namespace(as_json=False, field_name="AccountNameUpper__c")
        out = bdt_analyze.cmd_field_trace(self.bdt, args)
        self.assertIn("AccountNameUpper__c", out)
        # Defined by FORMULA0
        self.assertIn("FORMULA0", out)
        # Back-trace reaches the load
        self.assertIn("LOAD_DATASET0", out)
        # Shows the expression
        self.assertIn("upper(ssot__Name__c)", out)

    def test_trace_field_defined_in_load(self):
        args = argparse.Namespace(as_json=False, field_name="ssot__Id__c")
        out = bdt_analyze.cmd_field_trace(self.bdt, args)
        self.assertIn("LOAD_DATASET0", out)

    def test_trace_unknown_field(self):
        args = argparse.Namespace(as_json=False, field_name="NOPE__c")
        with self.assertRaises(bdt_analyze.BdtNotFoundError) as cm:
            bdt_analyze.cmd_field_trace(self.bdt, args)
        self.assertIn("NOPE__c", str(cm.exception))

    def test_trace_json(self):
        args = argparse.Namespace(as_json=True, field_name="AccountNameUpper__c")
        data = json.loads(bdt_analyze.cmd_field_trace(self.bdt, args))
        self.assertEqual(data["field"], "AccountNameUpper__c")
        self.assertTrue(any(e["node"] == "FORMULA0" for e in data["definitions"]))


class TestFieldTraceFocus(unittest.TestCase):
    """field-trace should narrow upstream deps to the specific field, not
    dump all fields consumed by the defining node."""

    def test_output_node_only_reports_source_of_mapped_field(self):
        # In minimal.json OUTPUT0 has 2 field mappings; tracing one targetField
        # should list only that mapping's sourceField as the dep, not both.
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=True, field_name="Name_Upper__c")
        data = json.loads(bdt_analyze.cmd_field_trace(bdt, args))
        # Find the entry where the definer is OUTPUT0
        output_defs = [d for d in data["definitions"] if d["node"] == "OUTPUT0"]
        if output_defs:
            # Only AccountNameUpper__c should be listed as an upstream dep,
            # NOT ssot__Id__c (which maps to ssot__Id__c target, unrelated to Name_Upper__c).
            deps = output_defs[0]["upstream_deps"]
            self.assertIn("AccountNameUpper__c", deps)
            self.assertNotIn("ssot__Id__c", deps)

    def test_formula_node_reports_only_fields_in_that_expression(self):
        # FORMULA0 in minimal.json has one output field AccountNameUpper__c
        # with expression upper(ssot__Name__c). Tracing AccountNameUpper__c
        # should show exactly ssot__Name__c as a dep.
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=True, field_name="AccountNameUpper__c")
        data = json.loads(bdt_analyze.cmd_field_trace(bdt, args))
        formula_defs = [d for d in data["definitions"] if d["node"] == "FORMULA0"]
        self.assertEqual(len(formula_defs), 1)
        deps = formula_defs[0]["upstream_deps"]
        self.assertIn("ssot__Name__c", deps)

    def test_compute_relative_reports_partition_and_order_fields(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "window_and_aggregate.json")
        args = argparse.Namespace(as_json=True, field_name="OrderRank__c")
        data = json.loads(bdt_analyze.cmd_field_trace(bdt, args))
        rank_defs = [d for d in data["definitions"] if d["node"] == "RANK_ORDERS"]
        self.assertEqual(len(rank_defs), 1)
        deps = rank_defs[0]["upstream_deps"]
        # partitionBy field
        self.assertIn("ssot__AccountId__c", deps)
        # orderBy field
        self.assertIn("ssot__CreatedDate__c", deps)

    def test_aggregate_reports_only_source_of_matching_aggregation(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "window_and_aggregate.json")
        args = argparse.Namespace(as_json=True, field_name="TotalAmount__c")
        data = json.loads(bdt_analyze.cmd_field_trace(bdt, args))
        agg_defs = [d for d in data["definitions"] if d["node"] == "AGG_BY_ACCOUNT"]
        self.assertEqual(len(agg_defs), 1)
        deps = agg_defs[0]["upstream_deps"]
        # Only the SUM source — not the COUNT source, not the groupings.
        self.assertIn("ssot__GrandTotalAmount__c", deps)
        self.assertNotIn("ssot__Id__c", deps)


class TestWindowAndAggregateTrace(unittest.TestCase):
    def setUp(self):
        self.bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "window_and_aggregate.json")

    def test_order_rank_defined_by_compute_relative(self):
        args = argparse.Namespace(as_json=False, field_name="OrderRank__c")
        out = bdt_analyze.cmd_field_trace(self.bdt, args)
        self.assertIn("RANK_ORDERS", out)
        self.assertIn("row_number()", out)
        # Partition and order are reported as upstream deps
        self.assertIn("ssot__AccountId__c", out)
        self.assertIn("ssot__CreatedDate__c", out)

    def test_total_amount_traces_through_aggregate(self):
        args = argparse.Namespace(as_json=False, field_name="TotalAmount__c")
        out = bdt_analyze.cmd_field_trace(self.bdt, args)
        # AGG_BY_ACCOUNT produces TotalAmount__c
        self.assertIn("AGG_BY_ACCOUNT", out)
        self.assertIn("SUM", out)
        self.assertIn("ssot__GrandTotalAmount__c", out)

    def test_aggregate_groupings_carried_through(self):
        # AccountId__c → ssot__AccountId__c passes from aggregate output through output mapping
        args = argparse.Namespace(as_json=False, field_name="AccountId__c")
        out = bdt_analyze.cmd_field_trace(self.bdt, args)
        self.assertIn("OUTPUT_SUMMARY", out)
        self.assertIn("ssot__AccountId__c", out)


class TestFormulaSubcommand(unittest.TestCase):
    def test_formula_of_formula_node(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False, node_name="FORMULA0")
        out = bdt_analyze.cmd_formula(bdt, args)
        self.assertIn("FORMULA0", out)
        self.assertIn("upper(ssot__Name__c)", out)
        # Upstream field `ssot__Name__c` is defined by LOAD_DATASET0
        self.assertIn("ssot__Name__c", out)
        self.assertIn("LOAD_DATASET0", out)

    def test_formula_of_compute_relative(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "window_and_aggregate.json")
        args = argparse.Namespace(as_json=False, node_name="RANK_ORDERS")
        out = bdt_analyze.cmd_formula(bdt, args)
        self.assertIn("row_number()", out)
        self.assertIn("partitionBy", out)
        self.assertIn("ssot__AccountId__c", out)

    def test_formula_of_non_formula_node_rejects(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False, node_name="LOAD_DATASET0")
        with self.assertRaises(bdt_analyze.BdtInputError):
            bdt_analyze.cmd_formula(bdt, args)

    def test_formula_unknown_node(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        args = argparse.Namespace(as_json=False, node_name="NOPE")
        with self.assertRaises(bdt_analyze.BdtNotFoundError):
            bdt_analyze.cmd_formula(bdt, args)


class TestInputShapeDetection(unittest.TestCase):
    """Parser accepts both the editor-export shape and the Connect API create payload shape."""

    def test_editor_export_shape_still_works(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        self.assertEqual(len(bdt.nodes), 3)
        # No outer wrapper metadata
        self.assertIsNone(bdt.name)
        self.assertIsNone(bdt.data_transform_type)
        # `definitions` is always non-empty; length 1 for editor-export.
        self.assertEqual(bdt.definition_count, 1)

    def test_api_input_single_definition(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "api_input_single.json")
        self.assertEqual(bdt.name, "TestTransform")
        self.assertEqual(bdt.label, "Test Transform")
        self.assertEqual(bdt.data_transform_type, "BATCH")
        self.assertEqual(bdt.data_space_name, "default")
        self.assertEqual(bdt.definition_count, 1)
        self.assertEqual(bdt.definition_index, 0)
        # Nodes accessible at top of DataTransform
        self.assertIn("LOAD_X", bdt.nodes)
        self.assertIn("OUTPUT_X", bdt.nodes)
        # Version from the definition (not the wrapper)
        self.assertEqual(bdt.version, "66.0")
        # No warnings for single-definition
        self.assertEqual(bdt.warnings(), [])

    def test_api_input_multi_definition(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "api_input_multi.json")
        self.assertEqual(bdt.definition_count, 2)
        self.assertEqual(bdt.definition_index, 0)
        # Descends into first definition by default
        self.assertIn("LOAD_A", bdt.nodes)
        self.assertNotIn("LOAD_B", bdt.nodes)
        # Multi-definition no longer emits a "first-only" warning — the parser
        # now exposes every definition and the CLI has a `--definition N` flag.
        self.assertEqual(bdt.warnings(), [])

    def test_unknown_shape_raises(self):
        with self.assertRaises(bdt_analyze.BdtInputError) as cm:
            bdt_analyze.DataTransform.from_dict({"name": "MyTransform", "label": "L"})
        self.assertIn("Expected 'nodes'", str(cm.exception))

    def test_all_subcommands_work_on_api_input(self):
        """summary, stages, lineage, field-trace should all work on the API-wrapped BDT."""
        import io, contextlib
        for subcmd, extra_arg in [("summary", None), ("stages", None), ("nodes", None),
                                   ("sources", None), ("outputs", None),
                                   ("lineage", "OUTPUT_X"), ("node", "LOAD_X")]:
            with self.subTest(subcmd=subcmd):
                argv = [subcmd, str(FIXTURES / "api_input_single.json")]
                if extra_arg: argv.append(extra_arg)
                out = io.StringIO(); err = io.StringIO()
                try:
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        code = bdt_analyze.main(argv)
                except SystemExit as e:
                    code = e.code
                self.assertEqual(code, 0, f"Subcommand {subcmd} failed: {err.getvalue()}")


class TestMultiDefinition(unittest.TestCase):
    """Parser exposes every definition in a multi-definition payload, not just the first."""

    def setUp(self):
        self.bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "api_input_multi.json")

    def test_definitions_length(self):
        self.assertEqual(len(self.bdt.definitions), 2)
        self.assertEqual(self.bdt.definition_count, 2)
        # Default selected index is 0
        self.assertEqual(self.bdt.definition_index, 0)

    def test_default_selection_is_first(self):
        self.assertIn("LOAD_A", self.bdt.nodes)
        self.assertNotIn("LOAD_B", self.bdt.nodes)

    def test_select_second_definition(self):
        self.bdt.select_definition(1)
        self.assertEqual(self.bdt.definition_index, 1)
        self.assertIn("LOAD_B", self.bdt.nodes)
        self.assertNotIn("LOAD_A", self.bdt.nodes)

    def test_select_out_of_range_raises(self):
        with self.assertRaises(bdt_analyze.BdtNotFoundError) as cm:
            self.bdt.select_definition(5)
        self.assertIn("out of range", str(cm.exception))

    def test_warnings_no_longer_mentions_first_only(self):
        # Previously warned "2 definitions; explains first only". No longer should.
        warnings = self.bdt.warnings()
        self.assertEqual(warnings, [])

    def test_definitions_subcommand_markdown(self):
        args = argparse.Namespace(as_json=False)
        out = bdt_analyze.cmd_definitions(self.bdt, args)
        self.assertIn("# Definitions", out)
        self.assertIn("| 0 |", out)
        self.assertIn("| 1 |", out)

    def test_definitions_subcommand_json(self):
        args = argparse.Namespace(as_json=True)
        data = json.loads(bdt_analyze.cmd_definitions(self.bdt, args))
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["index"], 0)
        self.assertEqual(data[1]["index"], 1)

    def test_definition_flag_routes_summary_to_second(self):
        """Full CLI smoke: --definition 1 makes summary operate on the second definition."""
        import io, contextlib
        argv = ["summary", "--definition", "1", str(FIXTURES / "api_input_multi.json")]
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = bdt_analyze.main(argv)
        except SystemExit as e:
            code = e.code
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("LOAD_B", out.getvalue())
        self.assertNotIn("LOAD_A", out.getvalue())

    def test_definition_flag_out_of_range_exits_2(self):
        import io, contextlib
        argv = ["summary", "--definition", "5", str(FIXTURES / "api_input_multi.json")]
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = bdt_analyze.main(argv)
        except SystemExit as e:
            code = e.code
        self.assertEqual(code, 2)
        self.assertIn("out of range", err.getvalue())

    def test_editor_export_has_single_definition(self):
        bdt = bdt_analyze.DataTransform.from_path(FIXTURES / "minimal.json")
        self.assertEqual(len(bdt.definitions), 1)
        self.assertEqual(bdt.definition_count, 1)
        # definitions subcommand on a single-definition input still works
        args = argparse.Namespace(as_json=False)
        out = bdt_analyze.cmd_definitions(bdt, args)
        self.assertIn("# Definitions", out)
        self.assertIn("| 0 |", out)


if __name__ == "__main__":
    unittest.main()
