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

    Copyright (C) 2016 Pascal Molin

******************************************************************************/

#include <string.h>
#include "acb_dirichlet.h"
#include "profiler.h"

#define LOG 0
#define CSV 1
#define JSON 2

typedef ulong (*do_f) (ulong q1, ulong q2);

static ulong
do_gcd(ulong q1, ulong q2)
{
    ulong n, q, k;

    for (n = 0, q = q1; q <= q2; q++)
        for (k = 1; k < q; k++)
            n += (n_gcd(k, q) == 1);

    return n;
}

static ulong
do_conrey(ulong q1, ulong q2)
{
    ulong n, q;

    for (n = 0, q = q1; q <= q2; q++)
    {
        acb_dirichlet_group_t G;
        acb_dirichlet_conrey_t x;

        acb_dirichlet_group_init(G, q);
        acb_dirichlet_conrey_init(x, G);

        acb_dirichlet_conrey_one(x, G);
        n++;

        for (; acb_dirichlet_conrey_next(x, G) >= 0; n++);
        acb_dirichlet_conrey_clear(x);
        acb_dirichlet_group_clear(G);
    }

    return n;
}

static ulong
do_chars(ulong q1, ulong q2)
{
    ulong n, q;

    for (n = 0, q = q1; q <= q2; q++)
    {
        acb_dirichlet_group_t G;
        acb_dirichlet_char_t chi;

        acb_dirichlet_group_init(G, q);
        acb_dirichlet_char_init(chi, G);

        acb_dirichlet_char_one(chi, G);
        n++;
        for (; acb_dirichlet_char_next(chi, G) >= 0; n++);

        acb_dirichlet_char_clear(chi);
        acb_dirichlet_group_clear(G);
    }

    return n;
}

static ulong
do_gcdpluscond(ulong q1, ulong q2)
{
    ulong n, q, k;

    for (n = 0, q = q1; q <= q2; q++)
    {
        acb_dirichlet_group_t G;
        acb_dirichlet_group_init(G, q);

        for (k = 1; k < q; k++)
        {
            /* known factors -> faster gcd */
            slong i;
            if (G->q_even > 1 && k % 2 == 0)
                continue;
            for (i = G->neven; i < G->num; i++)
                if (k % G->P[i].p == 0)
                    break;

            if (i == G->num)
                acb_dirichlet_ui_conductor(G, k);
        }

        n += G->phi_q;
        acb_dirichlet_group_clear(G);

    }

    return n;
}

int main(int argc, char *argv[])
{
    int out;
    ulong n, nref, maxq = 5000;

    int l, nf = 4;
    do_f func[4] = { do_gcd, do_conrey, do_chars, do_gcdpluscond };
    char * name[4] = { "gcd", "conrey", "chars", "gcd+cond" };

    int i, ni = 5;
    ulong qmin[5] = { 2,   1000, 10000, 100000, 1000000 };
    ulong qmax[5] = { 500, 3000, 11000, 100100, 1000010 };

    if (argc < 2)
        out = LOG;
    else if (!strcmp(argv[1], "json"))
        out = JSON;
    else if (!strcmp(argv[1], "csv"))
        out = CSV;
    else if (!strcmp(argv[1], "log"))
        out = LOG;
    else
    {
        printf("usage: %s [log|csv|json]\n", argv[0]);
        abort();
    }

    if (out == CSV)
        flint_printf("# %-6s, %7s, %7s, %7s\n","name", "qmin", "qmax", "time");

    for (i = 0; i < ni; i++)
    {

        if (out == LOG)
        {
            flint_printf("loop over all (Z/q)* for %wu<=q<=%wu\n", qmin[i], qmax[i]);
        }

        for (l = 0; l < nf; l++)
        {

            if (out == LOG)
                flint_printf("%-8s      ...  ",name[l]);
            else if (out == CSV)
                flint_printf("%-8s, %7d, %7d,   ",name[l],qmin[i],qmax[i]);
            else if (out == JSON)
                flint_printf("{ \"name\": \"%s\", \"qmin\": %d, \"qmax\": %d, \"time\": ",
                        name[l],qmin[i],qmax[i]);

            TIMEIT_ONCE_START
                (func[l])(qmin[i], qmax[i]);
            TIMEIT_ONCE_STOP

            if (l == 0)
                nref = n;
            else if (n != nref)
            {
                flint_printf("FAIL: wrong number of elements %wu != %wu\n\n",n, nref);
                abort();
            }

            if (out == JSON)
                flint_printf("}\n");
            else
                flint_printf("\n");
        }

    }

    flint_cleanup();
    return EXIT_SUCCESS;
}