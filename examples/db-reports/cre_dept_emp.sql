create table dept(
  deptno number(4) primary key
, dname varchar2(20)
, loc varchar2(20)
);

create table emp(
  empno number(4) primary key
, deptno number(4) not null
, constraint emp_fk foreign key (deptno) references dept (deptno)
, sal number not null
, comm number
, hiredate date
, ename varchar(20)
);

set define off

insert into dept(deptno,dname,loc) values (10, 'Distribution', 'Entenhausen');
insert into dept(deptno,dname,loc) values (20, 'Development', 'Hohenlimburg');
insert into dept(deptno,dname,loc) values (30, 'it-solutions', 'Entenhausen');
insert into dept(deptno,dname,loc) values (40, 'Public Relations', 'Gänsdorf');
insert into dept(deptno,dname,loc) values (50, 'Service', 'Entenhausen');

insert into emp(empno,deptno,ename,sal,comm,hiredate) values(1000, 10, 'Dagobert Duck', 9999, 1234, to_date('01.01.1988', 'DD.MM.YYYY'));
insert into emp(empno,deptno,ename,sal,comm,hiredate) values(1068, 20, 'Henning von Bargen', 2345, 50, to_date('01.01.1994', 'DD.MM.YYYY'));
insert into emp(empno,deptno,ename,sal,comm,hiredate) values(1002, 10, 'Gundel Gaukeley', 6543, 987, to_date('16.04.1989', 'DD.MM.YYYY'));
insert into emp(empno,deptno,ename,sal,comm,hiredate) values(1003, 50, 'Daisy Duck', 2222, null, to_date('01.07.2002', 'DD.MM.YYYY'));
insert into emp(empno,deptno,ename,sal,comm,hiredate) values(1004, 40, 'Donald Duck', 8765, 1111, to_date('01.09.1995', 'DD.MM.YYYY'));
insert into emp(empno,deptno,ename,sal,comm,hiredate) values(1005, 20, 'Daniel Düsentrieb', 2345, 50, to_date('01.09.1992', 'DD.MM.YYYY'));
insert into emp(empno,deptno,ename,sal,comm,hiredate) values(1006, 20, 'Dussel Duck', 2345, 50, to_date('01.09.1993', 'DD.MM.YYYY'));
