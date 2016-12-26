
start(<<16#ef, 16#bb>>, Handler, Stack, Config) ->
    incomplete(start, <<16#ef, 16#bb>>, Handler, Stack, Config);
start(<<16#ef>>, Handler, Stack, Config) ->
    incomplete(start, <<16#ef>>, Handler, Stack, Config);
start(<<>>, Handler, Stack, Config) ->
    incomplete(start, <<>>, Handler, Stack, Config);
start(Bin, Handler, Stack, Config) ->
    value(Bin, Handler, Stack, Config).
