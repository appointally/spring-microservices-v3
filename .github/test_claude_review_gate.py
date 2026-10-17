"""Exercise the public workflow's actual approval gate without credentials."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest
from unittest.mock import patch

WORKFLOW = Path(__file__).parent / 'workflows/claude-review.yml'


class ApprovalGateTest(unittest.TestCase):
    def run_gate(self, result=None, current='head', unresolved=False, api_failure=False, outcome='success'):
        if result is None:
            result = dict(complete=True, verdict='approved', reviewed_files=['file.txt'], findings=[], summary='Reviewed.')
        block = WORKFLOW.read_text().rsplit("python3 <<'PY'\n", 1)[1]
        script = textwrap.dedent(block).rsplit('\nPY', 1)[0]

        def gh(args, **kwargs):
            if api_failure:
                raise subprocess.CalledProcessError(1, args)
            if args[1:3] == ['api', 'graphql']:
                return json.dumps({'data': {'repository': {'pullRequest': {'reviewThreads': {
                    'pageInfo': {'hasNextPage': False}, 'nodes': [{'isResolved': not unresolved}]
                }}}}})
            return current + '\n'

        env = dict(REPO='owner/repo', PR='1', REVIEWED_SHA='head', REVIEW_OUTCOME=outcome, RESULT=json.dumps(result))
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, env):
            prior = Path.cwd()
            os.chdir(directory)
            try:
                Path('.claude-review').mkdir()
                Path('.claude-review/files.json').write_text('["file.txt"]')
                with patch('subprocess.check_output', side_effect=gh), patch('subprocess.run'):
                    exec(compile(script, str(WORKFLOW), 'exec'), {})
            finally:
                os.chdir(prior)

    def test_complete_approval_passes(self):
        self.run_gate()

    def test_partial_or_open_review_fails(self):
        valid = dict(complete=True, verdict='approved', reviewed_files=['file.txt'], findings=[], summary='Reviewed.')
        for changes in [dict(complete=False), dict(verdict='open'), dict(reviewed_files=[]),
                        dict(findings=['Unfixed problem']), dict(summary=''), dict(reviewed_files=[{}])]:
            with self.subTest(changes=changes), self.assertRaises(SystemExit):
                self.run_gate(dict(valid, **changes))

    def test_stale_head_unresolved_feedback_or_action_failure_blocks(self):
        for kwargs in [dict(current='new-head'), dict(unresolved=True), dict(outcome='failure')]:
            with self.subTest(kwargs=kwargs), self.assertRaises(SystemExit):
                self.run_gate(**kwargs)

    def test_api_failure_blocks(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_gate(api_failure=True)


if __name__ == '__main__':
    unittest.main()
