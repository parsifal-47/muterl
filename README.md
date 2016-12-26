# Muterl

Mutation testing for erlang

Supported mutators:
 - clause remove
 - logic change
 - constant change

Rebar-style configurable. Create muterl.config with erlang terms
in your project folder.

Default options are:

```erlang
{files, "src/*.erl"}.
{mutants, 100}.
{runner, "rebar eunit"}.
{report, "muterl.report"}.
{backup_folder, "muterl.backup"}.
```

To disable `remove_clause`, `logic_inverse` or `constant_change`, please
specify `{<mutation_name>, disable}.` at your config.

To selectively enable or disable mutations for a set of functions please specify
`{functions, "some?hing.*"}` or `{functions_skip, ".*test"}`. Function names matched with regexp. Both can be used at a time.

To use, run from your project folder, don't forget to backup everything!

Example below starts mutations for jsx:
```bash
git clone https://github.com/parsifal-47/muterl
git clone https://github.com/talentdeficit/jsx
cd jsx
../muterl/muterl
```

Feel free to create tickets and send your feedback!
