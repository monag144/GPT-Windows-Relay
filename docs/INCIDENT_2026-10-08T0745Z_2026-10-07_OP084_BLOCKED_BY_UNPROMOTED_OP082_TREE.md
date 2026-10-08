# Incident: OP084 blocked by unpromoted OP082 source — 2026-10-08T0745Z
OP084 correctly refused to stack rotation changes on dirty source left by failed OP082. OP085 backs up the complete dirty patch, restores promoted f82d39d, and resumes rotation from a clean rollback boundary.
