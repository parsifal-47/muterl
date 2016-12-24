# Muterl

Mutation testing for erlang

Supported mutators:
 - clause remove
 - logic change
 - constant change

Rebar-style configurable. Create muterl.conf with erlang terms
in your project folder.

Default options are:

  {files, "src/*.erl"}.
  {mutants, 100}.
  {runner, "./rebar eunit"}.
  {report, "muterl.report"}.
  {backup_folder, "muterl.backup"}.

To use, run from your project folder, don't forget to backup everything!

Feel free to create tickets and send your feedback!
