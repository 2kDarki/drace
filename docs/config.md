# Configuration

Drace supports both CLI-based and interactive configuration.

## Storage

Config values are persisted to `drace/defaults.json`.

## Common keys

- `mode`
- `line_len`
- `max_fn_steps`
- `max_coupling`
- `wrap`
- `color`
- `score`
- `only_rules`
- `ignored_rules`
- `ignored_files`
- `delay`

## CLI patterns

```bash
# list all config
drace config list

# show one key
drace config line_len
drace config show line_len

# set scalar
drace config line_len 100
drace config mode lint
drace config color on

# set/append/remove list values
drace config ignored_rules Z100 Z200
drace config ignored_rules + Z221
drace config ignored_rules - Z221

# reset
drace config reset line_len
drace config reset all
```

## Separators

Drace accepts flexible separators for assignment style:

- `=`
- `:`
- `::`

Example:

```bash
drace config line_len = 100
```

## Interactive mode

Run `drace config` with no extra arguments to open the menu interface.
