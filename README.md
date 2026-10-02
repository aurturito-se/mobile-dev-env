# mobile-dev-env
Conteneur de développement mobile (Flutter stable, Android SDK 34-36, JDK 17, Node, Python, xvfb, gh, outils glTF/images).
Image : ghcr.io/aurturito-se/mobile-dev-env:latest — déployée en stack Portainer inline, accès via `portainer_exec_container`.
Volumes : /workspace (projets), /cache (pub + gradle).
Pas d'émulateur Android (pas de /dev/kvm sur le VPS) : tests unitaires, goldens, analyse, builds APK/web.
