---
name: init-tenant
description: Initialize a new LMAP tenant with all required configuration files, directories, and consumer setup
disable-model-invocation: true
---

## Guard

Before doing anything, verify the `./etc` directory exists and is a git repository:
- Run `git -C ./etc rev-parse --git-dir`
- If it fails, stop and tell the user: **"The `./etc` repository is not present. Clone it first before initializing a tenant."**

## Required information

Gather from the user before proceeding (use `AskUserQuestion` for any missing values):

1. **Tenant name** — lowercase, no spaces or special characters (e.g. `vka`)
2. **Host** — which `mp-*` host it will be deployed to (e.g. `mp-1`)

## Host-to-IP mapping

Determine `config.ip` by reading an existing tenant's `services.php` on the same host. Look up which tenants are assigned to the target host in `.ci/config/inventory.yaml`, then read one of their `config/tenants/<name>/services.php` files to get the IP.

## Steps

For a tenant named `{name}` with PascalCase form `{Name}` on host `mp-{N}`:

### 1. Main repository files

| File | Action |
|---|---|
| `config/tenants/{name}/services.php` | Create — use template below |
| `tenants.yaml` | Add `- {name}` to the `tenants_webpack` list (before the blank line above `tenants_staging`) |
| `.ci/config/inventory.yaml` | Add `- 'tenant:{name}'` to the `mp-{N}` host block (before the `- 'host:mp-{N}'` line) |
| `public/maintenance/{name}.html` | Copy from any existing tenant (they are all identical) |
| `src/Tenants/{Name}/.gitkeep` | Create empty file |
| `translations/tenants/{name}/.gitkeep` | Create empty file |
| `translations/tenants_injections/{name}/.gitkeep` | Create empty file |

#### services.php template

```php
<?php

declare(strict_types=1);

use Symfony\Component\DependencyInjection\Loader\Configurator\ContainerConfigurator;
use function Symfony\Component\DependencyInjection\Loader\Configurator\param;

return static function (ContainerConfigurator $containerConfigurator): void {
    $parameters = $containerConfigurator->parameters();

    $parameters
        ->set('config.ip', '{IP}')
    ;

    $services = $containerConfigurator->services();

    $services->defaults()
        ->autowire()
        ->autoconfigure()
    ;

    $services->load('LMAP\\Tenants\\{Name}\\', param('kernel.tenant_namespace') . '/*')
        ->exclude([
            __DIR__ . '/**/{*Event.php}',
            __DIR__ . '/**/{Entity,Model,Repository}/*.php',
        ])
    ;
};
```

- `{Name}` = tenant name with first letter uppercase (e.g. `vka` → `Vka`)
- `{IP}` = the `config.ip` resolved from the host mapping step

### 2. etc repository — supervisord consumers

File: `etc/supervisord/consumers.conf`

Append the following block at the end of the file:

```ini

[group:{name}-prod]
programs=consumer-{name}-prod-async,consumer-{name}-prod-async-slow

[program:consumer-{name}-prod-async]
command=/ext/www/marketingportal/prod/current/bin/console messenger:consume async --time-limit=3600 --limit=10
user=www-data
numprocs=1
startsecs=0
autostart=false
autorestart=true
process_name=%(program_name)s_%(process_num)02d
stdout_logfile=/ext/www/logs_consumers/{name}_supervisor_consumer_async_prod.log
stderr_logfile=/ext/www/logs_consumers/{name}_supervisor_consumer_async_prod_error.log
environment=https_proxy="http://127.0.0.1:8060",http_proxy="http://127.0.0.1:8060",REMOTE=1,APP_ENV=prod,TENANT={name}

[program:consumer-{name}-prod-async-slow]
command=/ext/www/marketingportal/prod/current/bin/console messenger:consume async_slow --time-limit=7200 --limit=1
user=www-data
numprocs=1
startsecs=0
autostart=false
autorestart=true
process_name=%(program_name)s_%(process_num)02d
stdout_logfile=/ext/www/logs_consumers/{name}_supervisor_consumer_async_slow_prod.log
stderr_logfile=/ext/www/logs_consumers/{name}_supervisor_consumer_async_slow_prod_error.log
environment=https_proxy="http://127.0.0.1:8060",http_proxy="http://127.0.0.1:8060",REMOTE=1,APP_ENV=prod,TENANT={name}
```

### 3. Summary

After completing all steps, print a checklist of all created/modified files so the user can verify.

Note: the `etc/` directory is a separate git repository — remind the user that changes there need to be committed separately.
