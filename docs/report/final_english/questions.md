# Unresolved Questions and Evidence Boundaries

1. The separately supplied English instructor assignment description was not present in the repository or the attachments available to this run. The report uses the section mapping in the pasted final-report prompt plus the earlier four-part course requirement list and the supplied Chinese test-case template. If a different English assignment document exists, its requirement list should be compared with the report before submission.

2. The installed `academic-paper` skill has `version: 3.3.1` in its metadata while its routing contract describes `v3.9.2`. The required multi-agent folders and all requested modes are present, but this report does not claim a complete version-fingerprint match to 3.9.x. The discrepancy should be resolved if strict skill provenance is audited.

3. The repository and official-tool reference URLs are recorded in the report, but live HTTP resolution from this shell failed at the TLS layer. No new references were invented; the seven entries come from the repository's existing reference material and the named official projects. A browser-side resolver check remains advisable before final upload.

4. The transfer record does not contain CPU, memory, or storage identifiers. The report therefore omits hardware specifications and does not claim a cross-machine reproduction.

5. All 136 final run records mark formal verification as `skipped`. The 177 LTL clauses passed parser and proposition-mapping checks, but no model checker established program satisfaction.

6. Five task test-case copies differed from the frozen suite: P01, P08, P17, P18, and P19. P19 used an older emergency-stop polarity. The matrix was not rewritten because the submission had already run.

7. Three disputed tasks remain: P19, S11, and S05-06. Their case-level disputes should be resolved in a new frozen batch rather than used to overwrite the 136 recorded runs.

8. The original E3 budget check used UTF-8 byte length as a token-count stand-in. The report treats this as a known defect affecting budget termination; it does not silently patch the harness or rerun the matrix.

9. The title page leaves `[University, City, Postcode]`, `[Tel]`, and `[Email]` as highlighted placeholders because no verified institutional or contact details were supplied.
