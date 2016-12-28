# Muterl [![Build Status](https://travis-ci.org/parsifal-47/muterl.svg?branch=master)](https://travis-ci.org/parsifal-47/muterl)

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

If files can't be parsed due to compicated macros or parser bug - they are skipped.

While running, it creates a report for survived mutants, for example:

```erlang
Mutant survived, affected file: src/jsx_decoder.erl
*** muterl.backup/src/jsx_decoder.erl   2016-12-24 17:18:56.000000000 +0100
--- src/jsx_decoder.erl 2016-12-24 17:30:57.000000000 +0100
***************
*** 1114,1121 ****

  done(<<?space, Rest/binary>>, Handler, [], Config) ->
      done(Rest, Handler, [], Config);
- done(<<?newline, Rest/binary>>, Handler, [], Config) ->
-     done(Rest, Handler, [], Config);
  done(<<?tab, Rest/binary>>, Handler, [], Config) ->
      done(Rest, Handler, [], Config);
  done(<<?cr, Rest/binary>>, Handler, [], Config) ->
--- 1114,1119 ----
```

Feel free to create tickets and send your feedback!
