/*
    ctest.c  -  Don Cross <cosinekitty.com>

    C langauge unit test for Astronomy Engine project.
    https://cosinekitty.github.io/astronomy
*/

#include <stdio.h>
#include <string.h>
#include <math.h>
#include "astronomy.h"

#define PI      3.14159265358979323846

#define CHECK(x)            do{if(0 != (error = (x))) goto fail;}while(0)

static int CheckVector(int lnum, astro_vector_t v)
{
    if (v.status != ASTRO_SUCCESS)
    {
        fprintf(stderr, "FAILURE at ctest.c[%d]: vector status = %d\n", lnum, v.status);
        return 1;
    }
    return 0;
}

static int CheckEquator(int lnum, astro_equatorial_t equ)
{
    if (equ.status != ASTRO_SUCCESS)
    {
        fprintf(stderr, "FAILURE at ctest.c[%d]: equatorial status = %d\n", lnum, equ.status);
        return 1;
    }
    return 0;
}

#define CHECK_VECTOR(var,expr)   CHECK(CheckVector(__LINE__, ((var) = (expr))))
#define CHECK_EQU(var,expr)      CHECK(CheckEquator(__LINE__, ((var) = (expr))))

static int Test_AstroTime(void);
static int AstroCheck(void);
static int Diff(const char *c_filename, const char *js_filename);
static int DiffLine(int lnum, const char *cline, const char *jline, double *maxdiff, int *worst_lnum);
static int SeasonsTest(const char *filename);
static int MoonPhase(const char *filename);
static int RiseSet(const char *filename);
static int ElongationTest(void);

int main(int argc, const char *argv[])
{
    int error = 1;

    if (argc == 1)
    {
        CHECK(Test_AstroTime());
        CHECK(AstroCheck());
        goto success;
    }

    if (argc == 2)
    {
        const char *verb = argv[1];
        if (!strcmp(verb, "elongation"))
        {
            CHECK(ElongationTest());
            goto success;
        }
    }

    if (argc == 3)
    {
        const char *verb = argv[1];
        const char *filename = argv[2];

        if (!strcmp(verb, "seasons"))
        {
            CHECK(SeasonsTest(filename));
            goto success;
        }

        if (!strcmp(verb, "moonphase"))
        {
            CHECK(MoonPhase(filename));
            goto success;
        }

        if (!strcmp(verb, "riseset"))
        {
            CHECK(RiseSet(filename));
            goto success;
        }
    }

    if (argc == 4)
    {
        if (!strcmp(argv[1], "diff"))
        {
            const char *c_filename = argv[2];
            const char *js_filename = argv[3];
            CHECK(Diff(c_filename, js_filename));
            goto success;
        }
    }

    fprintf(stderr, "Invalid command line arguments.\n");
    error = 1;
    goto fail;

success:
    error = 0;

fail:
    fprintf(stderr, "ctest exiting with %d\n", error);
    return error;
}

static int Test_AstroTime(void)
{
    astro_time_t time;
    const double expected_ut = 6910.270978506945;
    const double expected_tt = 6910.271779431480;
    double diff;

    time = Astronomy_MakeTime(2018, 12, 2, 18, 30, 12.543);
    printf("Test_AstroTime: ut=%0.6lf, tt=%0.6lf\n", time.ut, time.tt);

    diff = time.ut - expected_ut;
    if (fabs(diff) > 1.0e-12)
    {
        fprintf(stderr, "Test_AstroTime: excessive UT error %lg\n", diff);
        return 1;
    }

    diff = time.tt - expected_tt;
    if (fabs(diff) > 1.0e-12)
    {
        fprintf(stderr, "Test_AstroTime: excessive TT error %lg\n", diff);
        return 1;
    }

    return 0;
}

static int AstroCheck(void)
{
    int error = 1;
    FILE *outfile = NULL;
    const char *filename = "temp/c_check.txt";
    astro_time_t time;
    astro_time_t stop;
    astro_body_t body;
    astro_vector_t pos;
    astro_equatorial_t j2000;
    astro_equatorial_t ofdate;
    astro_horizon_t hor;
    astro_observer_t observer = Astronomy_MakeObserver(29.0, -81.0, 10.0);
    int b;
    static const astro_body_t bodylist[] =  /* match the order in the JavaScript unit test */
    {
        BODY_SUN, BODY_MERCURY, BODY_VENUS, BODY_EARTH, BODY_MARS, 
        BODY_JUPITER, BODY_SATURN, BODY_URANUS, BODY_NEPTUNE, BODY_PLUTO
    };
    static int nbodies = sizeof(bodylist) / sizeof(bodylist[0]);

    outfile = fopen(filename, "wt");
    if (outfile == NULL)
    {
        fprintf(stderr, "AstroCheck: Cannot open output file: %s\n", filename);
        error = 1;
        goto fail;
    }

    fprintf(outfile, "o %lf %lf %lf\n", observer.latitude, observer.longitude, observer.height);

    time = Astronomy_MakeTime(1700, 1, 1, 0, 0, 0.0);
    stop = Astronomy_MakeTime(2200, 1, 1, 0, 0, 0.0);
    while (time.tt < stop.tt)
    {
        for (b=0; b < nbodies; ++b)
        {
            body = bodylist[b];
            CHECK_VECTOR(pos, Astronomy_HelioVector(body, time));
            fprintf(outfile, "v %s %0.16lf %0.16lf %0.16lf %0.16lf\n", Astronomy_BodyName(body), pos.t.tt, pos.x, pos.y, pos.z);

            if (body != BODY_EARTH)
            {
                CHECK_EQU(j2000, Astronomy_Equator(body, time, observer, 0, 0));
                CHECK_EQU(ofdate, Astronomy_Equator(body, time, observer, 1, 1));
                hor = Astronomy_Horizon(time, observer, ofdate.ra, ofdate.dec, REFRACTION_NONE);
                fprintf(outfile, "s %s %0.16lf %0.16lf %0.16lf %0.16lf %0.16lf %0.16lf %0.16lf\n", 
                    Astronomy_BodyName(body), time.tt, time.ut, j2000.ra, j2000.dec, j2000.dist, hor.azimuth, hor.altitude);
            }
        }

        CHECK_VECTOR(pos, Astronomy_GeoVector(BODY_MOON, time, 0));
        fprintf(outfile, "v GM %0.16lf %0.16lf %0.16lf %0.16lf\n", pos.t.tt, pos.x, pos.y, pos.z);

        CHECK_EQU(j2000, Astronomy_Equator(BODY_MOON, time, observer, 0, 0));
        CHECK_EQU(ofdate, Astronomy_Equator(BODY_MOON, time, observer, 1, 1));
        hor = Astronomy_Horizon(time, observer, ofdate.ra, ofdate.dec, REFRACTION_NONE);
        fprintf(outfile, "s GM %0.16lf %0.16lf %0.16lf %0.16lf %0.16lf %0.16lf %0.16lf\n", 
            time.tt, time.ut, j2000.ra, j2000.dec, j2000.dist, hor.azimuth, hor.altitude);

        time = Astronomy_AddDays(time, 10.0 + PI/100.0);
    }

fail:
    if (outfile != NULL)
        fclose(outfile);
    return error;
}

/*-----------------------------------------------------------------------------------------------------------*/

static int Diff(const char *c_filename, const char *js_filename)
{
    int error = 1;
    int lnum;
    FILE *cfile = NULL;
    FILE *jfile = NULL;
    char cline[200];
    char jline[200];
    char *cread;
    char *jread;
    double maxdiff = 0.0;
    int worst_lnum = 0;

    cfile = fopen(c_filename, "rt");
    if (cfile == NULL)
    {
        fprintf(stderr, "ctest(Diff): Cannot open input file: %s\n", c_filename);
        error = 1;
        goto fail;
    }

    jfile = fopen(js_filename, "rt");
    if (jfile == NULL)
    {
        fprintf(stderr, "ctest(Diff): Cannot open input file: %s\n", js_filename);
        error = 1;
        goto fail;
    }

    lnum = 0;
    for(;;)
    {
        cread = fgets(cline, sizeof(cline), cfile);
        jread = fgets(jline, sizeof(jline), jfile);
        if (cread==NULL && jread==NULL)
            break;      /* normal end of both files */
        
        if (cread==NULL || jread==NULL)
        {
            fprintf(stderr, "ctest(Diff): Files do not have same number of lines: %s and %s\n", c_filename, js_filename);
            error = 1;
            goto fail;
        }

        ++lnum;
        CHECK(DiffLine(lnum, cline, jline, &maxdiff, &worst_lnum));
    }

    printf("ctest(Diff): Maximum numeric difference = %lg, worst line number = %d\n", maxdiff, worst_lnum);
    if (maxdiff > 1.8e-12)
    {
        fprintf(stderr, "ERROR: Excessive error comparing files %s and %s\n", c_filename, js_filename);
        error = 1;
        goto fail;
    }

    error = 0;

fail:
    if (cfile != NULL) fclose(cfile);
    if (jfile != NULL) fclose(jfile);
    return error;
}

static int DiffLine(int lnum, const char *cline, const char *jline, double *maxdiff, int *worst_lnum)
{
    int error = 1;
    char cbody[10];
    char jbody[10];
    double cdata[7];
    double jdata[7];
    double diff;
    int i, nc, nj, nrequired = -1;

    /* be paranoid: make sure we can't possibly have a fake match. */
    memset(cdata, 0xdc, sizeof(cdata));
    memset(jdata, 0xce, sizeof(jdata));

    /* Make sure the two data records are the same type. */
    if (cline[0] != jline[0])
    {
        fprintf(stderr, "ctest(DiffLine): Line %d mismatch record type: '%c' vs '%c'.\n", lnum, cline[0], jline[0]);
        error = 1;
        goto fail;
    }

    switch (cline[0])
    {
    case 'o':       /* observer */
        nc = sscanf(cline, "o %lf %lf %lf", &cdata[0], &cdata[1], &cdata[2]);
        nj = sscanf(jline, "o %lf %lf %lf", &jdata[0], &jdata[1], &jdata[2]);
        cbody[0] = jbody[0] = '\0';
        nrequired = 3;
        break;

    case 'v':       /* heliocentric vector */
        nc = sscanf(cline, "v %9[A-Za-z] %lf %lf %lf", cbody, &cdata[0], &cdata[1], &cdata[2]);
        nj = sscanf(jline, "v %9[A-Za-z] %lf %lf %lf", jbody, &jdata[0], &jdata[1], &jdata[2]);
        nrequired = 4;
        break;

    case 's':       /* sky coords: ecliptic and horizontal */
        nc = sscanf(cline, "s %9[A-Za-z] %lf %lf %lf %lf %lf %lf %lf", cbody, &cdata[0], &cdata[1], &cdata[2], &cdata[3], &cdata[4], &cdata[5], &cdata[6]);
        nj = sscanf(jline, "s %9[A-Za-z] %lf %lf %lf %lf %lf %lf %lf", jbody, &jdata[0], &jdata[1], &jdata[2], &jdata[3], &jdata[4], &jdata[5], &jdata[6]);
        nrequired = 8;
        break;

    default:
        fprintf(stderr, "ctest(DiffLine): Line %d type '%c' is not a valid record type.\n", lnum, cline[0]);
        error = 1;
        goto fail;
    }

    if (nc != nj)
    {
        fprintf(stderr, "ctest(DiffLine): Line %d mismatch data counts: %d vs %d\n", lnum, nc, nj);
        error = 1;
        goto fail;
    }

    if (nc != nrequired)
    {
        fprintf(stderr, "ctest(DiffLine): Line %d incorrect number of scanned arguments: %d\n", lnum, nc);
        error = 1;
        goto fail;
    }

    if (strcmp(cbody, jbody))
    {
        fprintf(stderr, "ctest(DiffLine): Line %d body mismatch: '%s' vs '%s'\n.", lnum, cbody, jbody);
        error = 1;
        goto fail;
    }

    if (cbody[0])
    {
        /* This is one of the record types that contains a body name. */
        /* Therefore, we need to correct the number of numeric data. */
        --nrequired;
    }

    /* Verify all the numeric data are very close. */
    for (i=0; i < nrequired; ++i)
    {
        diff = fabs(cdata[i] - jdata[i]);
        if (diff > *maxdiff)
        {
            *maxdiff = diff;
            *worst_lnum = lnum;
        }
    }
    error = 0;

fail:
    return error;
}

/*-----------------------------------------------------------------------------------------------------------*/

static int SeasonsTest(const char *filename)
{
    int error = 1;
    int lnum;
    FILE *infile = NULL;
    char line[200];
    int nscanned, year, month, day, hour, minute;
    int current_year = 0;
    char name[20];
    astro_time_t correct_time;
    astro_time_t calc_time;
    astro_seasons_t seasons;
    double diff_minutes, max_minutes = 0.0;
    int mar_count=0, jun_count=0, sep_count=0, dec_count=0;

    memset(&seasons, 0, sizeof(seasons));    

    infile = fopen(filename, "rt");
    if (infile == NULL)
    {
        fprintf(stderr, "SeasonsTest: Cannot open input file: %s\n", filename);
        error = 1;
        goto fail;
    }

    lnum = 0;
    while (fgets(line, sizeof(line), infile))
    {
        ++lnum;
        /*
            2019-01-03T05:20Z Perihelion
            2019-03-20T21:58Z Equinox
            2019-06-21T15:54Z Solstice
            2019-07-04T22:11Z Aphelion
            2019-09-23T07:50Z Equinox
            2019-12-22T04:19Z Solstice
        */
        nscanned = sscanf(line, "%d-%d-%dT%d:%dZ %10[A-Za-z]", &year, &month, &day, &hour, &minute, name);
        if (nscanned != 6)
        {
            fprintf(stderr, "SeasonsTest: %s line %d : scanned %d, expected 6\n", filename, lnum, nscanned);
            error = 1;
            goto fail;
        }

        if (year != current_year)
        {
            current_year = year;
            seasons = Astronomy_Seasons(year);
            if (seasons.status != ASTRO_SUCCESS)
            {
                fprintf(stderr, "SeasonsTest: Astronomy_Seasons(%d) returned %d\n", year, seasons.status);
                error = 1;
                goto fail;
            }
        }

        memset(&calc_time, 0xcd, sizeof(calc_time));
        correct_time = Astronomy_MakeTime(year, month, day, hour, minute, 0.0);
        if (!strcmp(name, "Equinox"))
        {
            switch (month)
            {
            case 3:
                calc_time = seasons.mar_equinox;
                ++mar_count;
                break;
            case 9:
                calc_time = seasons.sep_equinox;
                ++sep_count;
                break;
            default:
                fprintf(stderr, "SeasonsTest: Invalid equinox date in test data: %s line %d\n", filename, lnum);
                error = 1;
                goto fail;
            }
        }
        else if (!strcmp(name, "Solstice"))
        {
            switch (month)
            {
            case 6:
                calc_time = seasons.jun_solstice;
                ++jun_count;
                break;
            case 12:
                calc_time = seasons.dec_solstice;
                ++dec_count;
                break;
            default:
                fprintf(stderr, "SeasonsTest: Invalid solstice date in test data: %s line %d\n", filename, lnum);
                error = 1;
                goto fail;
            }
        }
        else if (!strcmp(name, "Aphelion"))
        {
            /* not yet calculated */
            continue;
        }
        else if (!strcmp(name, "Perihelion"))
        {
            /* not yet calculated */
            continue;
        }
        else
        {
            fprintf(stderr, "SeasonsTest: %s line %d: unknown event type '%s'\n", filename, lnum, name);
            error = 1;
            goto fail;
        }

        /* Verify that the calculated time matches the correct time for this event. */
        diff_minutes = (24.0 * 60.0) * fabs(calc_time.tt - correct_time.tt);
        if (diff_minutes > max_minutes)
            max_minutes = diff_minutes;

        if (diff_minutes > 1.7)
        {
            fprintf(stderr, "SeasonsTest: %s line %d: excessive error (%s): %lf minutes.\n", filename, lnum, name, diff_minutes);
            error = 1;
            goto fail;
        }
    }

    printf("SeasonsTest: verified %d lines from file %s : max error minutes = %0.3lf\n", lnum, filename, max_minutes);
    printf("SeasonsTest: Event counts: mar=%d, jun=%d, sep=%d, dec=%d\n", mar_count, jun_count, sep_count, dec_count);
    error = 0;

fail:
    if (infile != NULL) fclose(infile);
    return error;
}

/*-----------------------------------------------------------------------------------------------------------*/

static int MoonPhase(const char *filename)
{
    int error = 1;
    FILE *infile = NULL;
    int lnum, nscanned;
    int quarter, year, month, day, hour, minute;
    int expected_quarter, quarter_count = 0;
    int prev_year = 0;
    double second, expected_elong;
    astro_time_t expected_time, start_time;
    astro_angle_result_t result;
    double degree_error, arcmin, max_arcmin = 0.0;
    double diff_seconds, maxdiff = 0.0;
    const double threshold_seconds = 120.0; /* max tolerable prediction error in seconds */
    astro_moon_quarter_t mq;
    char line[200];    

    memset(&mq, 0xcd, sizeof(mq));

    infile = fopen(filename, "rt");
    if (infile == NULL)
    {
        fprintf(stderr, "MoonPhase: Cannot open input file '%s'\n", filename);
        error = 1;
        goto fail;
    }

    /*
        0 1800-01-25T03:21:00.000Z
        1 1800-02-01T20:40:00.000Z
        2 1800-02-09T17:26:00.000Z
        3 1800-02-16T15:49:00.000Z
    */
    lnum = 0;
    while (fgets(line, sizeof(line), infile))
    {
        ++lnum;
        nscanned = sscanf(line, "%d %d-%d-%dT%d:%d:%lfZ", &quarter, &year, &month, &day, &hour, &minute, &second);
        if (nscanned != 7)
        {
            fprintf(stderr, "MoonPhase(%s line %d): Invalid data format\n", filename, lnum);
            error = 1;
            goto fail;
        }

        if (quarter < 0 || quarter > 3)
        {
            fprintf(stderr, "MoonPhase(%s line %d): Invalid quarter %d\n", filename, lnum, quarter);
            error = 1;
            goto fail;
        }

        expected_elong = 90.0 * quarter;
        expected_time = Astronomy_MakeTime(year, month, day, hour, minute, second);
        result = Astronomy_MoonPhase(expected_time);
        degree_error = fabs(result.angle - expected_elong);
        if (degree_error > 180.0)
            degree_error = 360 - degree_error;
        arcmin = 60.0 * degree_error;
        if (arcmin > 1.0)
        {
            fprintf(stderr, "MoonPhase(%s line %d): EXCESSIVE ANGULAR ERROR: %lg arcmin\n", filename, lnum, arcmin);
            error = 1;
            goto fail;
        }
        if (arcmin > max_arcmin)
            max_arcmin = arcmin;

        if (year != prev_year)
        {
            prev_year = year;
            /* The test data contains a single year's worth of data for every 10 years. */
            /* Every time we see the year value change, it breaks continuity of the phases. */            
            /* Start the search over again. */
            start_time = Astronomy_MakeTime(year, 1, 1, 0, 0, 0.0);
            mq = Astronomy_SearchMoonQuarter(start_time);
            expected_quarter = -1;  /* we have no idea what the quarter should be */
        }
        else
        {
            /* Yet another lunar quarter in the same year. */
            expected_quarter = (1 + mq.quarter) % 4;        /* expect the next consecutive quarter */
            mq = Astronomy_NextMoonQuarter(mq);
        }

        if (mq.status != ASTRO_SUCCESS)
        {
            fprintf(stderr, "MoonPhase(%s line %d): Astronomy_SearchMoonQuarter returned %d\n", filename, lnum, mq.status);
            error = 1;
            goto fail;
        }

        /* Make sure we find the next expected quarter. */
        if (expected_quarter != -1)
        {
            if (expected_quarter != mq.quarter)
            {
                fprintf(stderr, "MoonPhase(%s line %d): Astronomy_SearchMoonQuarter returned quarter %d, but expected %d\n", filename, lnum, quarter, expected_quarter);
                error = 1;
                goto fail;
            }
            ++quarter_count;
        }

        /* Make sure the time matches what we expect. */
        diff_seconds = fabs(mq.time.tt - expected_time.tt) * (24.0 * 3600.0);
        if (diff_seconds > threshold_seconds)
        {
            fprintf(stderr, "MoonPhase(%s line %d): excessive time error %0.3lf seconds\n", filename, lnum, diff_seconds);
            error = 1;
            goto fail;
        }

        if (diff_seconds > maxdiff)
            maxdiff = diff_seconds;
    }

    printf("MoonPhase: passed %d lines for file %s : max_arcmin = %0.6lf, maxdiff = %0.3lf seconds, %d quarters\n", lnum, filename, max_arcmin, maxdiff, quarter_count);
    error = 0;

fail:
    if (infile != NULL) fclose(infile);
    return error;
}

/*-----------------------------------------------------------------------------------------------------------*/

static int TestElongFile(const char *filename, double targetRelLon)
{
    int error = 1;
    FILE *infile = NULL;
    int lnum;
    char line[100];
    char name[20];
    int year, month, day, hour, minute;
    int nscanned;
    astro_time_t search_date, expected_time;
    astro_body_t body;
    astro_search_result_t search_result;
    double diff_minutes;

    infile = fopen(filename, "rt");
    if (infile == NULL)
    {
        fprintf(stderr, "TestElongFile: Cannot open input file: %s\n", filename);
        error = 1;
        goto fail;
    }

    lnum = 0;
    while (fgets(line, sizeof(line), infile))
    {
        ++lnum;

        /* 2018-05-09T00:28Z Jupiter */
        nscanned = sscanf(line, "%d-%d-%dT%d:%dZ %9[A-Za-z]", &year, &month, &day, &hour, &minute, name);
        if (nscanned != 6)
        {
            fprintf(stderr, "TestElongFile(%s line %d): Invalid data format.\n", filename, lnum);
            error = 1;
            goto fail;
        }

        body = Astronomy_BodyCode(name);
        if (body == BODY_INVALID)
        {
            fprintf(stderr, "TestElongFile(%s line %d): Invalid body name '%s'\n", filename, lnum, name);
            error = 1;
            goto fail;
        }

        search_date = Astronomy_MakeTime(year, 1, 1, 0, 0, 0.0);
        expected_time = Astronomy_MakeTime(year, month, day, hour, minute, 0.0);
        search_result = Astronomy_SearchRelativeLongitude(body, targetRelLon, search_date);
        if (search_result.status != ASTRO_SUCCESS)
        {
            fprintf(stderr, "TestElongFile(%s line %d): SearchRelativeLongitude returned %d\n", filename, lnum, search_result.status);
            error = 1;
            goto fail;
        }

        diff_minutes = (24.0 * 60.0) * (search_result.time.tt - expected_time.tt);
        printf("TestElongFile: %-7s error = %6.3lf minutes, iterations = %3d\n", name, diff_minutes, search_result.iter);
        if (fabs(diff_minutes) > 15.0)
        {
            fprintf(stderr, "TestElongFile(%s line %d): EXCESSIVE ERROR\n", filename, lnum);
            error = 1;
            goto fail;
        }
    }

    printf("TestElongFile: passed %d rows of data\n", lnum);
    error = 0;

fail:
    if (infile != NULL) fclose(infile);
    return error;
}

typedef struct
{
    astro_body_t        body;
    const char         *searchDate;
    const char         *eventDate;
    double              angle;
    astro_visibility_t  visibility;
}
elong_test_t;

static const elong_test_t ElongTestData[] =
{
    /* Max elongation data obtained from: */
    /* http://www.skycaramba.com/greatest_elongations.shtml */
    { BODY_MERCURY, "2010-01-17T05:22Z", "2010-01-27T05:22Z", 24.80, VISIBLE_MORNING },
    { BODY_MERCURY, "2010-05-16T02:15Z", "2010-05-26T02:15Z", 25.10, VISIBLE_MORNING },
    { BODY_MERCURY, "2010-09-09T17:24Z", "2010-09-19T17:24Z", 17.90, VISIBLE_MORNING },
    { BODY_MERCURY, "2010-12-30T14:33Z", "2011-01-09T14:33Z", 23.30, VISIBLE_MORNING },
    { BODY_MERCURY, "2011-04-27T19:03Z", "2011-05-07T19:03Z", 26.60, VISIBLE_MORNING },
    { BODY_MERCURY, "2011-08-24T05:52Z", "2011-09-03T05:52Z", 18.10, VISIBLE_MORNING },
    { BODY_MERCURY, "2011-12-13T02:56Z", "2011-12-23T02:56Z", 21.80, VISIBLE_MORNING },
    { BODY_MERCURY, "2012-04-08T17:22Z", "2012-04-18T17:22Z", 27.50, VISIBLE_MORNING },
    { BODY_MERCURY, "2012-08-06T12:04Z", "2012-08-16T12:04Z", 18.70, VISIBLE_MORNING },
    { BODY_MERCURY, "2012-11-24T22:55Z", "2012-12-04T22:55Z", 20.60, VISIBLE_MORNING },
    { BODY_MERCURY, "2013-03-21T22:02Z", "2013-03-31T22:02Z", 27.80, VISIBLE_MORNING },
    { BODY_MERCURY, "2013-07-20T08:51Z", "2013-07-30T08:51Z", 19.60, VISIBLE_MORNING },
    { BODY_MERCURY, "2013-11-08T02:28Z", "2013-11-18T02:28Z", 19.50, VISIBLE_MORNING },
    { BODY_MERCURY, "2014-03-04T06:38Z", "2014-03-14T06:38Z", 27.60, VISIBLE_MORNING },
    { BODY_MERCURY, "2014-07-02T18:22Z", "2014-07-12T18:22Z", 20.90, VISIBLE_MORNING },
    { BODY_MERCURY, "2014-10-22T12:36Z", "2014-11-01T12:36Z", 18.70, VISIBLE_MORNING },
    { BODY_MERCURY, "2015-02-14T16:20Z", "2015-02-24T16:20Z", 26.70, VISIBLE_MORNING },
    { BODY_MERCURY, "2015-06-14T17:10Z", "2015-06-24T17:10Z", 22.50, VISIBLE_MORNING },
    { BODY_MERCURY, "2015-10-06T03:20Z", "2015-10-16T03:20Z", 18.10, VISIBLE_MORNING },
    { BODY_MERCURY, "2016-01-28T01:22Z", "2016-02-07T01:22Z", 25.60, VISIBLE_MORNING },
    { BODY_MERCURY, "2016-05-26T08:45Z", "2016-06-05T08:45Z", 24.20, VISIBLE_MORNING },
    { BODY_MERCURY, "2016-09-18T19:27Z", "2016-09-28T19:27Z", 17.90, VISIBLE_MORNING },
    { BODY_MERCURY, "2017-01-09T09:42Z", "2017-01-19T09:42Z", 24.10, VISIBLE_MORNING },
    { BODY_MERCURY, "2017-05-07T23:19Z", "2017-05-17T23:19Z", 25.80, VISIBLE_MORNING },
    { BODY_MERCURY, "2017-09-02T10:14Z", "2017-09-12T10:14Z", 17.90, VISIBLE_MORNING },
    { BODY_MERCURY, "2017-12-22T19:48Z", "2018-01-01T19:48Z", 22.70, VISIBLE_MORNING },
    { BODY_MERCURY, "2018-04-19T18:17Z", "2018-04-29T18:17Z", 27.00, VISIBLE_MORNING },
    { BODY_MERCURY, "2018-08-16T20:35Z", "2018-08-26T20:35Z", 18.30, VISIBLE_MORNING },
    { BODY_MERCURY, "2018-12-05T11:34Z", "2018-12-15T11:34Z", 21.30, VISIBLE_MORNING },
    { BODY_MERCURY, "2019-04-01T19:40Z", "2019-04-11T19:40Z", 27.70, VISIBLE_MORNING },
    { BODY_MERCURY, "2019-07-30T23:08Z", "2019-08-09T23:08Z", 19.00, VISIBLE_MORNING },
    { BODY_MERCURY, "2019-11-18T10:31Z", "2019-11-28T10:31Z", 20.10, VISIBLE_MORNING },
    { BODY_MERCURY, "2010-03-29T23:32Z", "2010-04-08T23:32Z", 19.40, VISIBLE_EVENING },
    { BODY_MERCURY, "2010-07-28T01:03Z", "2010-08-07T01:03Z", 27.40, VISIBLE_EVENING },
    { BODY_MERCURY, "2010-11-21T15:42Z", "2010-12-01T15:42Z", 21.50, VISIBLE_EVENING },
    { BODY_MERCURY, "2011-03-13T01:07Z", "2011-03-23T01:07Z", 18.60, VISIBLE_EVENING },
    { BODY_MERCURY, "2011-07-10T04:56Z", "2011-07-20T04:56Z", 26.80, VISIBLE_EVENING },
    { BODY_MERCURY, "2011-11-04T08:40Z", "2011-11-14T08:40Z", 22.70, VISIBLE_EVENING },
    { BODY_MERCURY, "2012-02-24T09:39Z", "2012-03-05T09:39Z", 18.20, VISIBLE_EVENING },
    { BODY_MERCURY, "2012-06-21T02:00Z", "2012-07-01T02:00Z", 25.70, VISIBLE_EVENING },
    { BODY_MERCURY, "2012-10-16T21:59Z", "2012-10-26T21:59Z", 24.10, VISIBLE_EVENING },
    { BODY_MERCURY, "2013-02-06T21:24Z", "2013-02-16T21:24Z", 18.10, VISIBLE_EVENING },
    { BODY_MERCURY, "2013-06-02T16:45Z", "2013-06-12T16:45Z", 24.30, VISIBLE_EVENING },
    { BODY_MERCURY, "2013-09-29T09:59Z", "2013-10-09T09:59Z", 25.30, VISIBLE_EVENING },
    { BODY_MERCURY, "2014-01-21T10:00Z", "2014-01-31T10:00Z", 18.40, VISIBLE_EVENING },
    { BODY_MERCURY, "2014-05-15T07:06Z", "2014-05-25T07:06Z", 22.70, VISIBLE_EVENING },
    { BODY_MERCURY, "2014-09-11T22:20Z", "2014-09-21T22:20Z", 26.40, VISIBLE_EVENING },
    { BODY_MERCURY, "2015-01-04T20:26Z", "2015-01-14T20:26Z", 18.90, VISIBLE_EVENING },
    { BODY_MERCURY, "2015-04-27T04:46Z", "2015-05-07T04:46Z", 21.20, VISIBLE_EVENING },
    { BODY_MERCURY, "2015-08-25T10:20Z", "2015-09-04T10:20Z", 27.10, VISIBLE_EVENING },
    { BODY_MERCURY, "2015-12-19T03:11Z", "2015-12-29T03:11Z", 19.70, VISIBLE_EVENING },
    { BODY_MERCURY, "2016-04-08T14:00Z", "2016-04-18T14:00Z", 19.90, VISIBLE_EVENING },
    { BODY_MERCURY, "2016-08-06T21:24Z", "2016-08-16T21:24Z", 27.40, VISIBLE_EVENING },
    { BODY_MERCURY, "2016-12-01T04:36Z", "2016-12-11T04:36Z", 20.80, VISIBLE_EVENING },
    { BODY_MERCURY, "2017-03-22T10:24Z", "2017-04-01T10:24Z", 19.00, VISIBLE_EVENING },
    { BODY_MERCURY, "2017-07-20T04:34Z", "2017-07-30T04:34Z", 27.20, VISIBLE_EVENING },
    { BODY_MERCURY, "2017-11-14T00:32Z", "2017-11-24T00:32Z", 22.00, VISIBLE_EVENING },
    { BODY_MERCURY, "2018-03-05T15:07Z", "2018-03-15T15:07Z", 18.40, VISIBLE_EVENING },
    { BODY_MERCURY, "2018-07-02T05:24Z", "2018-07-12T05:24Z", 26.40, VISIBLE_EVENING },
    { BODY_MERCURY, "2018-10-27T15:25Z", "2018-11-06T15:25Z", 23.30, VISIBLE_EVENING },
    { BODY_MERCURY, "2019-02-17T01:23Z", "2019-02-27T01:23Z", 18.10, VISIBLE_EVENING },
    { BODY_MERCURY, "2019-06-13T23:14Z", "2019-06-23T23:14Z", 25.20, VISIBLE_EVENING },
    { BODY_MERCURY, "2019-10-10T04:00Z", "2019-10-20T04:00Z", 24.60, VISIBLE_EVENING },
    { BODY_VENUS,   "2010-12-29T15:57Z", "2011-01-08T15:57Z", 47.00, VISIBLE_MORNING },
    { BODY_VENUS,   "2012-08-05T08:59Z", "2012-08-15T08:59Z", 45.80, VISIBLE_MORNING },
    { BODY_VENUS,   "2014-03-12T19:25Z", "2014-03-22T19:25Z", 46.60, VISIBLE_MORNING },
    { BODY_VENUS,   "2015-10-16T06:57Z", "2015-10-26T06:57Z", 46.40, VISIBLE_MORNING },
    { BODY_VENUS,   "2017-05-24T13:09Z", "2017-06-03T13:09Z", 45.90, VISIBLE_MORNING },
    { BODY_VENUS,   "2018-12-27T04:24Z", "2019-01-06T04:24Z", 47.00, VISIBLE_MORNING },
    { BODY_VENUS,   "2010-08-10T03:19Z", "2010-08-20T03:19Z", 46.00, VISIBLE_EVENING },
    { BODY_VENUS,   "2012-03-17T08:03Z", "2012-03-27T08:03Z", 46.00, VISIBLE_EVENING },
    { BODY_VENUS,   "2013-10-22T08:00Z", "2013-11-01T08:00Z", 47.10, VISIBLE_EVENING },
    { BODY_VENUS,   "2015-05-27T18:46Z", "2015-06-06T18:46Z", 45.40, VISIBLE_EVENING },
    { BODY_VENUS,   "2017-01-02T13:19Z", "2017-01-12T13:19Z", 47.10, VISIBLE_EVENING },
    { BODY_VENUS,   "2018-08-07T17:02Z", "2018-08-17T17:02Z", 45.90, VISIBLE_EVENING }
};

static const int ElongTestCount = sizeof(ElongTestData) / sizeof(ElongTestData[0]);

static int ParseDate(const char *text, astro_time_t *time)
{
    int year, month, day, hour, minute, nscanned;

    nscanned = sscanf(text, "%d-%d-%dT%d:%dZ", &year, &month, &day, &hour, &minute);
    if (nscanned != 5)
    {
        fprintf(stderr, "ParseDate: Invalid date text '%s'\n", text);
        time->ut = time->tt = NAN;
        return 1;
    }

    *time = Astronomy_MakeTime(year, month, day, hour, minute, 0.0);
    return 0;
}

static int TestMaxElong(const elong_test_t *test)
{
    int error;
    astro_time_t searchTime, eventTime;
    astro_elongation_t evt;
    double hour_diff, arcmin_diff;
    const char *name = NULL;
    const char *vis = NULL;

    switch (test->body)
    {
    case BODY_MERCURY:  name = "Mercury";   break;
    case BODY_VENUS:    name = "Venus";     break;
    default:
        fprintf(stderr, "TestMaxElong: invalid body %d in test data.\n", test->body);
        error = 1;
        goto fail;
    }

    switch (test->visibility)
    {
    case VISIBLE_MORNING:   vis = "morning";    break;
    case VISIBLE_EVENING:   vis = "evening";    break;
    default:
        fprintf(stderr, "TestMaxElong: invalid visibility %d in test data.\n", test->visibility);
        error = 1;
        goto fail;
    }

    CHECK(ParseDate(test->searchDate, &searchTime));
    CHECK(ParseDate(test->eventDate,  &eventTime));

    evt = Astronomy_SearchMaxElongation(test->body, searchTime);
    if (evt.status != ASTRO_SUCCESS)
    {
        fprintf(stderr, "TestMaxElong(%s %s): SearchMaxElongation returned %d\n", name, test->searchDate, evt.status);
        error = 1;
        goto fail;
    }

    hour_diff = 24.0 * fabs(evt.time.tt - eventTime.tt);
    arcmin_diff = 60.0 * fabs(evt.elongation - test->angle);

    printf("TestMaxElong: %-7s %-7s elong=%5.2lf (%4.2lf arcmin, %5.3lf hours)\n", name, vis, evt.elongation, arcmin_diff, hour_diff);

    if (hour_diff > 0.6)
    {
        fprintf(stderr, "TestMaxElong(%s %s): excessive hour error.\n", name, test->searchDate);
        error = 1;
        goto fail;
    }

    if (arcmin_diff > 3.1)
    {
        fprintf(stderr, "TestMaxElong(%s %s): excessive arcmin error.\n", name, test->searchDate);
        error = 1;
        goto fail;
    }

fail:
    return error;
}

static int SearchElongTest()
{
    int error = 1;
    int i;

    for (i=0; i < ElongTestCount; ++i)
        CHECK(TestMaxElong(&ElongTestData[i]));

    printf("SearchElongTest: Passed %d rows\n", ElongTestCount);
    error = 0;

fail:
    return error;
}

static int TestPlanetLongitudes(
    astro_body_t body, 
    const char *outFileName, 
    const char *zeroLonEventName)
{
    int error = 1;
    const int startYear = 1700;
    const int stopYear  = 2200;
    astro_time_t time, stopTime;
    double rlon = 0.0;
    const char *event;
    astro_search_result_t search_result;
    int count = 0;
    double day_diff, min_diff = 1.0e+99, max_diff = 1.0e+99, sum_diff = 0.0;
    astro_vector_t geo;
    double dist;
    FILE *outfile = NULL;
    const char *name;
    double ratio, thresh;

    name = Astronomy_BodyName(body);
    if (!name[0])
    {
        fprintf(stderr, "TestPlanetLongitudes: Invalid body code %d\n", body);
        error = 1;
        goto fail;
    }

    outfile = fopen(outFileName, "wt");
    if (outfile == NULL)
    {
        fprintf(stderr, "TestPlanetLongitudes: Cannot open output file: %s\n", outFileName);
        error = 1;
        goto fail;
    }

    time = Astronomy_MakeTime(startYear, 1, 1, 0, 0, 0.0);
    stopTime = Astronomy_MakeTime(stopYear, 1, 1, 0, 0, 0.0);
    while (time.tt < stopTime.tt)
    {
        ++count;
        event = (rlon == 0.0) ? zeroLonEventName : "sup";
        search_result = Astronomy_SearchRelativeLongitude(body, rlon, time);
        if (search_result.status != ASTRO_SUCCESS)
        {
            fprintf(stderr, "TestPlanetLongitudes(%s): SearchRelativeLongitude returned %d\n", name, search_result.status);
            error = 1;
            goto fail;
        }

        if (count >= 2)
        {
            /* Check for consistent intervals. */
            /* Mainly I don't want to skip over an event! */
            day_diff = search_result.time.tt - time.tt;
            sum_diff += day_diff;
            if (count == 2)
            {
                min_diff = max_diff = day_diff;
            }
            else
            {
                if (day_diff < min_diff) 
                    min_diff = day_diff;

                if (day_diff > max_diff) 
                    max_diff = day_diff;
            }
        }

        geo = Astronomy_GeoVector(body, search_result.time, 0);
        if (geo.status != ASTRO_SUCCESS)
        {
            fprintf(stderr, "TestPlanetLongitudes(%s): GeoVector returned %d\n", name, geo.status);
            error = 1;
            goto fail;
        }
        dist = Astronomy_VectorLength(geo);
        fprintf(outfile, "e %s %s %0.16lf %0.16lf\n", name, event, search_result.time.tt, dist);

        /* Search for the opposite longitude event next time. */
        time = search_result.time;
        rlon = 180.0 - rlon;
    }

    switch (body)
    {
    case BODY_MERCURY:  thresh = 1.65;  break;
    case BODY_MARS:     thresh = 1.30;  break;
    default:            thresh = 1.07;  break;
    }

    ratio = max_diff / min_diff;
    printf("TestPlanetLongitudes(%-7s): %5d events, ratio=%5.3lf, file: %s\n", name, count, ratio, outFileName);

    if (ratio > thresh)
    {
        fprintf(stderr, "TestPlanetLongitudes(%s): excessive event interval ratio.\n", name);
        error = 1;
        goto fail;
    }

    error = 0;
fail:
    if (outfile != NULL) fclose(outfile);
    return error;
}

static int ElongationTest(void)
{
    int error;

    CHECK(TestElongFile("longitude/opposition_2018.txt", 0.0));

    CHECK(TestPlanetLongitudes(BODY_MERCURY, "temp/c_longitude_Mercury.txt", "inf"));
    CHECK(TestPlanetLongitudes(BODY_VENUS,   "temp/c_longitude_Venus.txt",   "inf"));
    CHECK(TestPlanetLongitudes(BODY_MARS,    "temp/c_longitude_Mars.txt",    "opp"));
    CHECK(TestPlanetLongitudes(BODY_JUPITER, "temp/c_longitude_Jupiter.txt", "opp"));
    CHECK(TestPlanetLongitudes(BODY_SATURN,  "temp/c_longitude_Saturn.txt",  "opp"));
    CHECK(TestPlanetLongitudes(BODY_URANUS,  "temp/c_longitude_Uranus.txt",  "opp"));
    CHECK(TestPlanetLongitudes(BODY_NEPTUNE, "temp/c_longitude_Neptune.txt", "opp"));
    CHECK(TestPlanetLongitudes(BODY_PLUTO,   "temp/c_longitude_Pluto.txt",   "opp"));

    CHECK(SearchElongTest());

fail:
    return error;
}

/*-----------------------------------------------------------------------------------------------------------*/

static int RiseSet(const char *filename)
{
    int error = 1;
    FILE *infile = NULL;
    char line[100];
    char name[20];
    double longitude, latitude;
    int year, month, day, hour, minute;
    char kind[2];       /* "r" or "s" for rise or set */
    int direction;      /* +1 for rise, -1 for set */
    int lnum, nscanned;

    infile = fopen(filename, "rt");
    if (infile == NULL)
    {
        fprintf(stderr, "RiseSet: cannot open input file: %s\n", filename);
        error = 1;
        goto fail;
    }

    lnum = 0;
    while (fgets(line, sizeof(line), infile))
    {
        ++lnum;

        // Moon  103 -61 1944-01-02T17:08Z s
        // Moon  103 -61 1944-01-03T05:47Z r
        nscanned = sscanf(line, "%9[A-Za-z] %lf %lf %d-%d-%dT%d:%dZ %1[rs]", 
            name, &longitude, &latitude, &year, &month, &day, &hour, &minute, kind);

        if (nscanned != 9)
        {
            fprintf(stderr, "RiseSet(%s line %d): invalid format\n", filename, lnum);
            error = 1;
            goto fail;
        }

        if (!strcmp(kind, "r"))
            direction = +1;
        else if (!strcmp(kind, "s"))
            direction = -1;
        else
        {
            fprintf(stderr, "RiseSet(%s line %d): invalid kind '%s'\n", filename, lnum, kind);
            error = 1;
            goto fail;
        }        

        (void)direction;    /* NOT YET FINISHED!!!!!!!!!! */
    }

    printf("RiseSet: passed %d lines\n", lnum);
    error = 0;
fail:
    if (infile != NULL) fclose(infile);
    return error;
}

/*-----------------------------------------------------------------------------------------------------------*/
