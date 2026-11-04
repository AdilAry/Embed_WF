---
name: new-project
description: Create a new ESP32 project from the Embed_WF template, make the first commit and (optionally) a GitHub repository. Use when the owner wants to start a new embedded project.
argument-hint: <project-name>
disable-model-invocation: true
---

# New embedded project

Project name requested: `$ARGUMENTS`

1. If no name was given, ask for one (lowercase, digits, `-`). It becomes the folder and GitHub repo name.
2. Run `new-embedded-project <name>`. It creates `~/projects/<name>` from the template and commits.
   If the command is missing, run `bash ~/Embed_WF/tools/new_project.sh <name>` instead.
3. Ask the owner: **private or public GitHub repo?** Explain briefly: public = anyone can see it and
   GitHub Actions minutes are unlimited; private = only them, with a monthly free CI allowance that is
   plenty for hobby use. Then run, inside the project folder:
   `gh repo create <name> --private|--public --source . --push`
   If `gh` is not logged in, tell the owner to run `gh auth login` and stop.
4. Run `make host-test` in the project to prove the copy works.
5. Tell the owner the next steps, exactly:
   - `cd ~/projects/<name>`
   - write the idea in `docs/IDEA.md` (plain words, 5–15 sentences)
   - start `claude` in that folder and run `/define`

Do not start writing the FSD or any code in this skill.
