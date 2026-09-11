export { auth as middleware } from "./auth"

export const config = {
  // Protect all routes except login, api, and static files
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|login).*)"],
}
