Name:		reflectasm
Version:	1.09
Release:	1
Summary:	Bytecode-generated Java reflection
Group:		Development/Java
License:	BSD-3-Clause
URL:		https://github.com/EsotericSoftware/reflectasm
# Tag 1.09. The POM in that tag still says 1.08. Vendored junit is removed.
# Java sources are stored with LF line endings so the patch applies.
Source0:	https://github.com/EsotericSoftware/reflectasm/archive/refs/tags/1.09.tar.gz#/reflectasm-1.09.tar.gz
# ASM 9 rejects compressed stack frames in class files older than V1_6.
# The generator still emits F_SAME frames, so the generated class is V1_8.
Patch0:		reflectasm-1.09-asm9-classversion.patch

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	mvn(org.ow2.asm:asm)

%description
ReflectASM builds field, method, and constructor accessors with ASM
instead of java.lang.reflect. Kryo 2.24.0 links this unshaded jar
against the system ASM. The upstream shaded classifier is not shipped.

%prep
%autosetup -n reflectasm-%{version} -p1
find . -name '*.jar' -delete

%build
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
mkdir -p classes
find src -name '*.java' > sources.list
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp %{_javadir}/asm.jar \
	-d classes @sources.list
jar cf reflectasm.jar -C classes .
cat > reflectasm.pom <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.esotericsoftware.reflectasm</groupId>
  <artifactId>reflectasm</artifactId>
  <version>%{version}</version>
  <name>ReflectASM</name>
  <description>High performance Java reflection using code generation.</description>
  <url>https://github.com/EsotericSoftware/reflectasm</url>
  <licenses>
    <license>
      <name>BSD-3-Clause</name>
      <url>https://opensource.org/license/bsd-3-clause</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.ow2.asm</groupId>
      <artifactId>asm</artifactId>
      <version>9.11.1</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact reflectasm.pom:reflectasm.jar \
	--file-name reflectasm \
	--filelist .mfiles

%check
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
JAR=%{buildroot}%{_javadir}/reflectasm.jar
test -f "$JAR"
mkdir -p check
cat > check/Smoke.java <<'END'
import com.esotericsoftware.reflectasm.ConstructorAccess;
import com.esotericsoftware.reflectasm.FieldAccess;
import com.esotericsoftware.reflectasm.MethodAccess;

public class Smoke {
	public int value;

	public int bump(int n) {
		return value + n;
	}

	public static void main(String[] args) {
		FieldAccess fields = FieldAccess.get(Smoke.class);
		Smoke sample = new Smoke();
		fields.set(sample, "value", Integer.valueOf(7));
		if (!Integer.valueOf(7).equals(fields.get(sample, "value"))) {
			throw new AssertionError("field");
		}
		MethodAccess methods = MethodAccess.get(Smoke.class);
		if (!Integer.valueOf(10).equals(methods.invoke(sample, "bump", Integer.valueOf(3)))) {
			throw new AssertionError("method");
		}
		if (ConstructorAccess.get(Smoke.class).newInstance() == null) {
			throw new AssertionError("constructor");
		}
		System.out.println("reflectasm_ok");
	}
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp "$JAR:%{_javadir}/asm.jar" -d check check/Smoke.java
test "$(java -cp "check:$JAR:%{_javadir}/asm.jar" Smoke)" = reflectasm_ok

%files -f .mfiles
%doc license.txt README.md
