"""📦 core/ — Building blocks universales del sistema

✨ ¿Qué pertenece aquí?
   • Value Objects matemáticos/lógicos reusables en CUALQUIER dominio:
     - PositiveValue, NonEmptyString, Duration, Percentage
   • Tipos primitivos validados
   • Helpers genéricos SIN dependencia de negocio

🚫 ¿Qué NO pertenece aquí?
   • Entidades específicas del dominio (AudioSegment, Transcript, User, Payment)
   • Reglas de negocio (NormalizeAudio, DetectSilence, ProcessPayment)
   • Cualquier concepto que solo tenga sentido en TU proyecto

✅ Dónde poner lo específico del dominio:
   → modules/{bounded_context}/domain/

💡 Principio preventivo:
   Si no podrías reusar este código en un sistema de pagos O un e-commerce,
   probablemente NO pertenece a core/.

📚 Referencia: "Make core truly universal — not a dumping ground for shared code"
   — Adaptado de Vaughn Vernon, Implementing Domain-Driven Design
"""
