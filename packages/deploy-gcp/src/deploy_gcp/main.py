import argparse
import os
import shutil
import subprocess


# Context
def get_project_root():
    current_file = os.path.abspath(__file__)
    return os.path.abspath(
        os.path.join(os.path.dirname(current_file), "..", "..", "..", "..")
    )


PROJECT_ROOT = get_project_root()
APPS_API_DIR = os.path.join(PROJECT_ROOT, "apps", "api")

# Defaults
DEFAULT_REGION = "us-central1"
DEFAULT_FUNCTION_NAME = "interlock-api"


def get_env_or_arg(arg_val, env_var, prompt_text, default=None):
    if arg_val:
        return arg_val
    val = os.getenv(env_var)
    if val:
        return val
    if default:
        return default
    return input(f"{prompt_text}: ")


def main():
    parser = argparse.ArgumentParser(description="Deploy Interlock API to Cloud Run")
    parser.add_argument("--project-id", help="GCP Project ID")
    parser.add_argument("--region", help="GCP Region", default=DEFAULT_REGION)
    parser.add_argument(
        "--function-name", help="Service Name", default=DEFAULT_FUNCTION_NAME
    )
    # Kept for compatibility but unused
    parser.add_argument("--bucket", help="Unused for Cloud Run source deploy")
    parser.add_argument(
        "--update", action="store_true", help="Unused (deploy always updates)"
    )
    args = parser.parse_args()

    project_id = get_env_or_arg(
        args.project_id, "GCP_PROJECT_ID", "Enter GCP Project ID"
    )
    region = get_env_or_arg(
        args.region, "GCP_REGION", "Enter GCP Region", DEFAULT_REGION
    )
    function_name = args.function_name

    print(f"Deploying {function_name} to {project_id}/{region}...")
    print(f"Project Root: {PROJECT_ROOT}")

    # Check if necessary dirs exist
    if not os.path.exists(APPS_API_DIR):
        print(f"Error: API directory not found at {APPS_API_DIR}")
        return

    # 1. Prepare build directory
    build_dir = os.path.join(PROJECT_ROOT, "build_deploy")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)

    try:
        # 2. Copy API code
        print("Copying API code...")
        for item in os.listdir(APPS_API_DIR):
            if item in [
                "build",
                "__pycache__",
                ".venv",
                "start.sh",
                "local_deploy.sh",
                "source.zip",
                ".DS_Store",
            ]:
                continue
            src = os.path.join(APPS_API_DIR, item)
            dst = os.path.join(build_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        # 3. Copy monorepo packages (flattened)
        print("Copying monorepo packages...")
        packages_dir = os.path.join(PROJECT_ROOT, "packages")
        for pkg_name in ["core", "parsers"]:
            src_layout_path = os.path.join(packages_dir, pkg_name, "src", pkg_name)

            src_path = None
            if os.path.exists(src_layout_path):
                src_path = src_layout_path
            elif os.path.exists(os.path.join(packages_dir, pkg_name, pkg_name)):
                src_path = os.path.join(packages_dir, pkg_name, pkg_name)

            dst_pkg_path = os.path.join(build_dir, pkg_name)

            if src_path:
                print(f"  Copying {pkg_name} from {src_path}")
                shutil.copytree(src_path, dst_pkg_path)
            else:
                print(f"  Warning: Source for package {pkg_name} not found. Skipping.")

        # 4. Generate requirements.txt
        print("Generating requirements.txt...")
        req_path = os.path.join(build_dir, "requirements.txt")
        cmd = [
            "uv",
            "export",
            "--package",
            "api",
            "--no-dev",
            "--format",
            "requirements-txt",
            "--no-hashes",
            "--output-file",
            req_path,
        ]
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)

        # Filter local package paths
        with open(req_path) as f:
            lines = f.readlines()

        with open(req_path, "w") as f:
            for line in lines:
                line = line.strip()
                if "file://" in line and ("parser" in line or "core" in line):
                    continue
                if line.startswith("-e"):
                    continue
                if not line:
                    continue
                f.write(line + "\n")

            # Ensure wrapper dependencies
            f.write("uvicorn>=0.20.0\n")

        # 5. Generate Dockerfile
        print("Generating Dockerfile...")
        dockerfile_path = os.path.join(build_dir, "Dockerfile")
        with open(dockerfile_path, "w") as f:
            f.write("FROM python:3.12-slim\n")
            f.write("WORKDIR /app\n")
            f.write("COPY . .\n")
            f.write("RUN pip install --no-cache-dir -r requirements.txt\n")
            f.write(
                'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]\n'
            )

        # 6. Deploy to Cloud Run
        print(f"Deploying to Cloud Run service {function_name} in {region}...")

        deploy_cmd = [
            "gcloud",
            "run",
            "deploy",
            function_name,
            "--source",
            build_dir,
            "--project",
            project_id,
            "--region",
            region,
            "--allow-unauthenticated",
            "--memory",
            "1Gi",
            # "--clear-base-image", # Only needed for migration from Buildpacks
            "--quiet",
        ]

        subprocess.run(deploy_cmd, check=True)

        print("Service deployed successfully to Cloud Run.")

    except subprocess.CalledProcessError as e:
        print(f"Deployment failed: {e}")

    except Exception as e:
        print(f"Error during deployment preparation: {e}")

    finally:
        # Cleanup
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)


if __name__ == "__main__":
    main()
