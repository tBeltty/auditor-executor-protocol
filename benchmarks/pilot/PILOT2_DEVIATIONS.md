# Pilot 2 deviations log

1. Model and effort were constant across all runs: DeepSeek 4.1 Flash, effort High, launched by Orca through OpenCode. The only operational
   change was the provider endpoint behind that model, switched partway through when the original endpoint reached a usage limit. The model weights
   and effort setting are the same; the switch point is visible in `results/pilot2_driver.log`.
2. Prompt format. N and AE prompts spell out the negative-control procedure step by step (Pilot 1 wording, adapted to the CRM guard groups). The user
   noted this measures prompt wording as much as the protocol. Not changed mid-pilot to keep comparability; proposed fix for a next pilot: give N and AE
   the protocol document itself as context, with an identical base prompt for all workflows.
