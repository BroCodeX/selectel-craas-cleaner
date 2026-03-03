from loguru import logger
from cleanup_rules_parser import split_images_by_rules


def select_images_to_delete(repo_name, images, cleanup_rules, default_keep_latest):
    sorted_images = sorted(images, key=lambda x: x.get("createdAt", ""), reverse=True)
    grouped, unmatched = split_images_by_rules(repo_name, sorted_images, cleanup_rules)

    to_delete = []

    for rule_name, rule_images in grouped.items():
        rule = cleanup_rules.get(rule_name, {})
        keep_latest = int(rule.get("keep_latest", default_keep_latest))
        logger.info(f"Rule: {rule_name}, matched images: {len(rule_images)}, keep latest: {keep_latest}")

        if len(rule_images) > keep_latest:
            to_delete.extend(rule_images[keep_latest:])
        else:
            logger.info(f"Rule '{rule_name}' matched {len(rule_images)} images, keep latest: {default_keep_latest}, none to delete")

    if default_keep_latest is not None and len(unmatched) > default_keep_latest:
        to_delete.extend(unmatched[default_keep_latest:])
    else:
        logger.info(f"Unmatched images: {len(unmatched)}, keep latest: {default_keep_latest}, none to delete")        
    unique = []
    seen = set()
    for image in to_delete:
        digest = image.get("digest")
        if not digest or digest in seen:
            continue
        unique.append(image)
        seen.add(digest)

    return unique
