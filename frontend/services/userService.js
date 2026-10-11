/* ============================================================
   CampusQueue — User service
   All accounts in the database, for the admin Users page.
   ============================================================ */

const Users = {
  _list: [],
  async load() {
    const data = await Api.get("/api/admin/users");
    this._list = data.users || [];
  },
  /** @returns {Array<{ full_name, username, role, student_number, email }>} */
  list() { return this._list; },
};
