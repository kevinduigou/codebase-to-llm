# AGENTS.md

## Code Style
- **Immutability First**: 
   - Treat all function parameters as **immutable**. Never modify inputs directly.
   - Prefer pure functions and immutable objects with `@final` and `__slots__`.
- **Make Illegal States Unrepresentable**:
  - Domain objects must not allow invalid construction.
  - Use factory methods like `try_create()` or validation before instantiation.
  - Never expose public constructors for domain objects with constraints.
- **Be Explicit**: No dynamic behavior or magic (e.g., metaclasses, monkey patching, decorators that inject logic).
- **Explicit**: Function and variable names shall be as explicit as possible
- **Rust-style Control Flow**:
  - Use `try`, `except`, or `raise` only in the infrastructure layer to open file, send requests, ...
  - All fallible functions must return a `Result[T, E]` object (as definid in src/codebase_to_llm/domain/result.py).
- Use `ValueObject` and `Entity` base classes to distinguish object types as defined in DDD.
  - **ValueObject**: Immutable, compared by value.
  - **Entity**: Has `id`, compared by identity.
  - Example:
    ```python
    @final class EmailAddress(ValueObject): ...
    @final class User(Entity): ...
    ```
- Do not allow domain objects to depend on external libraries, ORMs, or I/O.

- When doing structural modification to the application, use clear separation of concern between the layers:
  - **Domain** under src/codebase_to_llm/domain: Core business logic. Immutable, pure. No DB, I/O, or HTTP code.
  - **Application** under src/codebase_to_llm/application: Use cases, orchestration. Talks to ports. Stateless.
  - **Infrastructure** under src/codebase_to_llm/infrastructure: Implements ports using DBs, APIs, or I/O.
  - **Interface** under src/codebase_to_llm/interface: Adapters for CLI, HTTP/REST/GraphQL, or React frontend.
- Define **ports (interfaces)** in the domain or application layer.
- Implement ports (adapters) in infrastructure.
-  Application Layer is the home of use cases, prefer uses cases over too general-purpose services.

## Buildng and Testing

- Once a modification is done on Python files, always perform 
uv run pytest then if it ok follow with
uv run ruff check ./src/ then if it ok follow with
uv run mypy ./src/ then if it ok follow with

and finish by
uv run black ./



