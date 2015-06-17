/*=============================================================================

    This file is part of ARB.

    ARB is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    ARB is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ARB; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

=============================================================================*/
/******************************************************************************

    Copyright (C) 2015 Fredrik Johansson

******************************************************************************/

#include "acb.h"

static void
acb_log_sin_pi_half(acb_t res, const acb_t z, long prec, int upper)
{
    acb_t t, u, zmid;
    arf_t n;
    arb_t pi;

    acb_init(t);
    acb_init(u);
    acb_init(zmid);
    arf_init(n);
    arb_init(pi);

    arf_set(arb_midref(acb_realref(zmid)), arb_midref(acb_realref(z)));
    arf_set(arb_midref(acb_imagref(zmid)), arb_midref(acb_imagref(z)));

    arf_floor(n, arb_midref(acb_realref(zmid)));

    arb_sub_arf(acb_realref(zmid), acb_realref(zmid), n, prec);

    acb_sin_pi(t, zmid, prec);
    acb_log(t, t, prec);

    arb_const_pi(pi, prec);

    if (upper)
        arb_submul_arf(acb_imagref(t), pi, n, prec);
    else
        arb_addmul_arf(acb_imagref(t), pi, n, prec);

    /* propagated error bound from the derivative pi cot(pi z) */
    if (!acb_is_exact(z))
    {
        mag_t zm, um;

        mag_init(zm);
        mag_init(um);

        acb_cot_pi(u, z, prec);
        acb_mul_arb(u, u, pi, prec);

        mag_hypot(zm, arb_radref(acb_realref(z)), arb_radref(acb_imagref(z)));
        acb_get_mag(um, u);
        mag_mul(um, um, zm);

        acb_add_error_mag(t, um);

        mag_clear(zm);
        mag_clear(um);
    }

    acb_set(res, t);

    acb_clear(t);
    acb_clear(u);
    acb_clear(zmid);
    arf_clear(n);
    arb_clear(pi);
}

void
acb_log_sin_pi(acb_t res, const acb_t z, long prec)
{
    if (!acb_is_finite(z))
    {
        acb_indeterminate(res);
        return;
    }

    if (arb_is_positive(acb_imagref(z)) ||
        (arb_is_zero(acb_imagref(z)) && arb_is_negative(acb_realref(z))))
    {
        acb_log_sin_pi_half(res, z, prec, 1);
    }
    else if (arb_is_negative(acb_imagref(z)) ||
        (arb_is_zero(acb_imagref(z)) && arb_is_positive(acb_realref(z))))
    {
        acb_log_sin_pi_half(res, z, prec, 0);
    }
    else
    {
        acb_t t;
        acb_init(t);
        acb_log_sin_pi_half(t, z, prec, 1);
        acb_log_sin_pi_half(res, z, prec, 0);
        arb_union(acb_realref(res), acb_realref(res), acb_realref(t), prec);
        arb_union(acb_imagref(res), acb_imagref(res), acb_imagref(t), prec);
        acb_clear(t);
    }
}
