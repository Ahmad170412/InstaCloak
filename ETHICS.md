# ETHICS — using InstaCloak responsibly

InstaCloak is an open-source OSINT (open-source intelligence) research tool.
This document is the project's ethical baseline: what the tool is *for*, the
lines it will not cross, and the obligations you take on when you run it.

Please read this before using InstaCloak. It is not legalese — it is the
operating manual for not becoming the problem you are investigating.

---

## 1. What this tool is for

InstaCloak collects **publicly visible data only** — the same pages any human
can open in a browser without an account. Legitimate use cases include:

- **Security research & threat intel** — profiling publicly-exposed accounts
  that impersonate brands or people, or that coordinate abuse.
- **Vetting & due diligence** — checking the authenticity of an account before
  trusting it (fake-follower detection, impersonation signals, engagement
  realism, public contact details).
- **Journalism & verification** — corroborating public claims with public
  posts, timestamps, and affiliations.
- **Personal safety** — researching a public account before interacting with
  it (dating, marketplaces, "influencers" offering services).
- **Education** — learning how public social data, and tools that collect it,
  actually work.

If your purpose isn't on this list, slow down and re-read the next section.

## 2. Lines this project will not cross

Some things are *technically possible* with this kind of tool. They are still
off-limits. InstaCloak is deliberately engineered to make several of them hard
or impossible:

- **No private-account access.** Private profiles return almost nothing, by
  design. We do not attempt to bypass privacy controls, and if a tool claims
  it can, that tool is lying or breaking the law.
- **No fabrication of data.** The report engine marks login-walled data as
  `walled` instead of inventing lists, and verifies that a follower dialog is
  a *real* list rather than Instagram's "suggested accounts" wall. Dishonest
  data is worse than no data.
- **No mass contact harvesting.** We will not add Osintgram-style features
  that bulk-collect the emails/phones of a target's followers. Those are third
  parties who never opted into being investigated. This is a hard scope line.
- **No stalking, doxxing, or harassment.** Do not use InstaCloak to track,
  intimidate, expose, or harass any person — public figure or not. Public
  data used to cause harm is still harm.
- **No targeting of protected characteristics.** Profiling or targeting people
  based on race, religion, sexual orientation, gender identity, health status,
  or political opinion is never acceptable, regardless of data availability.
- **No credential abuse.** Burner accounts are for *your own* anonymous
  browsing only — never for logging in as someone else, and never for actions
  that could get a real person's account flagged.

## 3. The law

Public does not mean consequence-free. You are responsible for the legal
framework you operate under:

- **Instagram's Terms of Service** — InstaCloak only reads public pages, but
  automated collection still technically violates Instagram's ToS. Account
  suspension is a real risk; that is why the tool is built around humanized,
  low-volume browsing.
- **Data protection law** — GDPR (EU), CCPA/CPRA (California), and similar
  regimes regulate the collection and processing of personal data, even from
  public sources. If you are processing EU/California residents' data at
  scale, you likely need a lawful basis beyond "it was public."
- **National laws** — computer-misuse and anti-stalking statutes differ by
  jurisdiction. What is tolerated research in one country can be a criminal
  offense in another.

**The tool is MIT-licensed and provided "AS IS"; you bear full responsibility
for how you use it.**

## 4. Operational principles

1. **Minimize.** Collect only what your question requires. Use
   `--max-posts`, `--no-media`, and `--no-followers` to keep runs lean.
2. **Keep provenance.** InstaCloak records *where* each datum came from and
   whether it was walled or served. Preserve that — it is what lets a finding
   be verified rather than asserted.
3. **Respect rate and volume.** "This is recon, not a firehose." Single
   targets, spaced-out runs, humanized timing. A run that hammers Instagram is
   both detectable and disproportionate.
4. **Don't retain longer than needed.** `output/` reports can contain personal
   data. Delete them when the investigation is over, and never commit them to
   version control (`.gitignore` already excludes them).
5. **Protect your burner.** Credentials live only in your local `config.toml`
   (permission 0600) or environment variables. Never commit, screenshot, or
   share them. A burner is a tool; treat it like one.
6. **Don't launder conclusions.** Public counts and engagement numbers change;
   a single snapshot is evidence, not a verdict. Report uncertainty
   (`unknown`, `walled`) as the tool does.

## 5. Ask before you run

Before every run, one honest question: **"Would I be comfortable with this
same data being collected about me, by a stranger, for this purpose?"**

If the answer is no, stop — regardless of whether the data is public. Public
visibility is not consent to surveillance, and "it was public" is the excuse
of every tool that ever became the problem.

## 6. Responsible disclosure

If you believe InstaCloak can be used to harm someone in a way this document
does not cover, or you find a bug that amplifies its reach, please open an
issue describing it rather than weaponizing it. If you are a platform
reporting abuse originating from this tool, include the run metadata from the
affected `report.json` so the operator can be identified.

---

*Public data, human touch. Use responsibly.*
