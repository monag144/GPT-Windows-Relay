# Incident — PCE15 content-script source/Client divergence — 2026-10-10T0118Z

## Trigger and evidence

PCE15.004 read-only localhost/content-script probe established source/Client mirror drift. PCE15.009 repeated and quantified the drift across all three matching paths.

- Working-tree repository `windows-relay/content.js`, `extension/content.js`, `extension-persistent/content.js`: identical SHA256 `8a1bd0222adf91e8a18062522aa854f189d54e907d7f979100577af97103597f`, 122,272 bytes and 3,022 lines each.
- Deployed `Client/Relay` copies: identical SHA256 `34500934b214423afc2d3c267877a961cd0ec46521e5860ed149502d7f4e2ae5`, 103,925 bytes and 2,746 lines each.
- All source-to-Client pairs differ in actual text beginning at line 56; whitespace-normalized text also differs. The tested diff had 64 replacement and 250 deletion line tallies (approximation from SequenceMatcher), no insert tally.
- Corresponding temporary/persistent manifests match by SHA and reference `content.js`.
- Source working-tree bytes did not equal `git show HEAD:windows-relay/content.js` although `git status --porcelain` showed no tracked changes. A Windows text-conversion filter or CRLF is a possible cause **not yet proven**.
- The actual loaded Firefox extension script SHA was not measured. No assertion of loaded runtime parity is justified.

## Severity and failed acceptance

**G04 FAIL (0/1 verified production parity acceptance)**. Deployed component version differs from development source; runtime loaded identity remains UNKNOWN. The situation illustrates the user's concern that piecemeal deployment can leave multiple conflicting builds. Merely passing isolated unit suites does not qualify deployed runtime.

## Safe disposition, not a code repair

No code, local checkout, Client tree, live Firefox, clipboard, or message was changed by PCE15.004 or .009. The protected PCE12 evidence files were verified intact. Prior `main` documentation audit baseline `3de89e5f44365dd2c2b537e9a260cb661474b132`.

Documented future path: verify exact GitHub canonical source, raw blob/working-tree filter interpretation, then build a coherent versioned release manifest and rollback as GitHub commits; pull SHA-pinned source to Windows; run targeted/full tests; deploy entire compatible Client set only after acceptance, with STOP and independent loaded-runtime confirmation. No local hotfix or patch during grading. **Incident open, release blocked.**
