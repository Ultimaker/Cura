import pytest
from pathlib import Path

# Small helper script to run the coverage of main code & all plugins

path = Path("plugins")
args = ["--cov" ,"cura" , "--cov-report", "html"]
all_paths = []
for p in path.glob('**/*'):
	if p.is_dir():
		if p.name in ["__pycache__", "tests"]:
			continue
		args.append("--cov")
		args.append(str(p))
		all_paths.append(str(p))

for path in all_paths:
	args.append(path)
args.append(".")
args.append("-x")
pytest.main(args)

