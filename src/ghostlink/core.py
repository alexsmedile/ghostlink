from ghostlink.cli.main import main
from ghostlink.domain.models import FindResult, LinkSpec
from ghostlink.domain.validation import validate_link_spec as validate_spec
from ghostlink.output.prompts import prompt_non_empty
from ghostlink.output.renderers import render_find_result
from ghostlink.services.link_service import load_bulk_specs, parse_bulk_line


def print_find_result(result: FindResult) -> None:
    print(render_find_result(result))


if __name__ == "__main__":
    raise SystemExit(main())
