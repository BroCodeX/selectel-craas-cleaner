from loguru import logger


def get_repositories(session, base_url, registry_id, token):
    logger.info("=== get_repositories() ===")

    url = f"{base_url}/registries/{registry_id}/repositories"
    res = session.get(url, headers={"X-Auth-Token": token}, timeout=15)

    logger.debug(f"Repo status: {res.status_code}")

    if res.status_code == 204:
        logger.warning("No repositories found (empty registry)")
        return []

    if res.status_code == 404:
        logger.warning(f"Registry {registry_id} not found")
        return []

    if res.status_code >= 500:
        logger.warning(f"Registry API server error {res.status_code}")
        return []

    res.raise_for_status()

    data = res.json()
    if not isinstance(data, list):
        logger.critical(f"Unexpected repositories response: {data}")
        return []

    logger.success(f"Repositories found: {len(data)}")
    return data


def get_images(session, base_url, registry_id, token, repo_name):
    logger.info(f"=== get_images() repo={repo_name} ===")

    url = f"{base_url}/registries/{registry_id}/repositories/{repo_name}/images"
    res = session.get(url, headers={"X-Auth-Token": token}, timeout=15)

    logger.debug(f"Images status {repo_name}: {res.status_code}")

    if res.status_code == 204:
        logger.warning(f"{repo_name}: no images")
        return []

    if res.status_code == 404:
        logger.warning(f"{repo_name}: repository not found")
        return []

    if res.status_code >= 500:
        logger.warning(f"{repo_name}: registry server error {res.status_code}")
        return []

    res.raise_for_status()

    data = res.json()
    if not isinstance(data, list):
        logger.critical(f"{repo_name}: unexpected images response {data}")
        return []

    logger.success(f"{repo_name}: images={len(data)}")
    return data


def delete_image(session, base_url, registry_id, token, repo_name, digest, dry_run):
    logger.info(f"=== delete_image() repo={repo_name} digest={digest} ===")

    if dry_run:
        logger.info(f"[DRY-RUN] Would delete {repo_name} {digest}")
        return

    url = f"{base_url}/registries/{registry_id}/repositories/{repo_name}/{digest}"
    res = session.delete(url, headers={"X-Auth-Token": token}, timeout=10)

    logger.debug(f"Delete status {digest}: {res.status_code}")

    if res.status_code == 204:
        logger.success(f"Deleted {repo_name} {digest}")
    else:
        logger.critical(f"Delete failed {digest}: {res.status_code} {res.text}")
