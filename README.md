# Prokopton

[![CI](https://github.com/leehart3000/prokopton/actions/workflows/ci.yml/badge.svg)](https://github.com/leehart3000/prokopton/actions/workflows/ci.yml)

**Prokopton** provides shared foundations for Prokopton projects, such as
[ProkoptonML](https://github.com/leehart3000/prokoptonml).

## Package

Prokopton is published as the `prokopton` package. Its shared code lives in
`prokopton.core`, part of the wider `prokopton` namespace:

```python
import prokopton.core
```

Other Prokopton packages add their own subpackages to the same namespace, for
example `prokopton.ml` from the `prokopton-ml` package.

## Status

This project is in early development.

## Licence

Copyright (C) 2026 Lee Hart

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, version 3 only.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the [LICENSE](LICENSE) file for details.

SPDX-License-Identifier: `AGPL-3.0-only`
