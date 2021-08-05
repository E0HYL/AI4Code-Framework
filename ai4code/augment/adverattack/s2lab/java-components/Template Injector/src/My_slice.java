import soot.*;
import soot.jimple.*;

import java.util.ArrayList;
import java.util.Iterator;

public class My_slice {
    private ArrayList<Local> my_locals;
    private ArrayList<Unit> my_units;
    private String feature = "tmp";
    private String name = "tmp";

    private Soot_utlilty utility = new Soot_utlilty();
    private static final double COMPLEXITY_RATIO=0.5;

    public My_slice(ArrayList<Local> my_locals, ArrayList<Unit> my_units) {
        this.my_locals = my_locals;
        this.my_units = my_units;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public ArrayList<Local> getMy_locals() {
        return my_locals;
    }

    public void setMy_locals(ArrayList<Local> my_locals) {
        this.my_locals = my_locals;
    }

    public ArrayList<Unit> getMy_units() {
        return my_units;
    }

    public void setMy_units(ArrayList<Unit> my_units) {
        this.my_units = my_units;
    }





    public ArrayList<Unit> clear_Unit_list(){
        ArrayList<Unit> to_ret = new ArrayList<>();
        for(Iterator<Unit> iter = getMy_units().iterator(); iter.hasNext();){
            Unit u = iter.next();
            boolean to_add = true;
            for(ValueBox vb : u.getUseAndDefBoxes()){
                if(vb.getValue() instanceof Local){
                    if(!in_Locals(vb.getValue())){
                        to_add= false;
                    }
                }
            }
            if(to_add) to_ret.add(u);
        }
        return to_ret;

    }



    public SootClass get_soot_class(String  n){

        SootClass sClass = new SootClass(n, Modifier.PUBLIC);
        sClass.setSuperclass(Scene.v().getSootClass("java.lang.Object"));
        SootMethod method = new SootMethod("tmp",
                null,
                VoidType.v(), Modifier.PUBLIC );
        Body b = Jimple.v().newBody(method);

        Local thisLocal = Jimple.v().newLocal("this", sClass.getType());
        b.getLocals().add(thisLocal);
        b.getUnits().add(Jimple.v().newIdentityStmt(thisLocal, Jimple.v().newThisRef(sClass.getType())));

        VirtualInvokeExpr vinvokeExpr = null;
        for(Local l: my_locals){
            b.getLocals().add(l);

            if(l.getType().toString().contains("android.content.Context")){
                try {
                    SootMethod get_context = Scene.v().getMethod("<android.content.Context: android.content.Context getApplicationContext()>");
                    vinvokeExpr = Jimple.v().newVirtualInvokeExpr(thisLocal, get_context.makeRef());
                    AssignStmt astmt = Jimple.v().newAssignStmt(l, vinvokeExpr);
                    b.getUnits().add(astmt);
                }catch (Exception e){}

            }
        }
        clear_Unit_list();
        for(Unit u : my_units){

            if(!b.getUnits().contains(u)) {
                b.getUnits().add(u);
            }

        }
        if(!(b.getUnits().getLast() instanceof ReturnVoidStmt)) {
            b.getUnits().add(Jimple.v().newReturnVoidStmt());
        }
        method.setActiveBody(b);

        System.out.println("body created\n"+b.toString());
        sClass.addMethod(method);
        b.validate();
        return  sClass;
    }

    private boolean in_Locals(Value to_check){
        for(Local  l: getMy_locals()){
            if(l.equals(to_check)){
                return true;
            }
        }
        return false;
    }


    public double slice_complexity_score(){
        int primitive =0;
        int complex=0;
        int instructions = my_units.size();
        ArrayList types= new ArrayList();
        for(Local l : my_locals){
            if(!types.contains(l.getType().toString())){
                types.add(l.getType().toString());
            }
            if(utility.isExcludeClass(l.getType().toString())){
                primitive++;
            }else {
                complex++;
            }
        }
        Jimple_utility ju = new Jimple_utility();
        int CC =ju.calculate_cyclomatic_complexity(this.get_soot_class("tmp"));
        return complex-(COMPLEXITY_RATIO*primitive)+types.size()+2*CC;
    }

    public int get_CC(){
        Jimple_utility ju = new Jimple_utility();
        return ju.calculate_cyclomatic_complexity(this.get_soot_class("tmp"));
    }



    @Override
    public String toString() {
        SootMethod method = new SootMethod("tmp",
                null,
                VoidType.v(), Modifier.PUBLIC );
        Body b = Jimple.v().newBody(method);
        for(Local l: my_locals){
            b.getLocals().add(l);
        }
        for(Unit u : my_units){
            if(!b.getUnits().contains(u)) {
                b.getUnits().add(u);
            }
        }
        return b.toString();
    }

    public void fix_this_ref(SootClass tmp_c) {
        Local thisLocal = Jimple.v().newLocal("this", tmp_c.getType());
        my_locals.add(thisLocal);
        SootMethod get_context = Scene.v().getMethod("<android.content.Context: android.content.Context getApplicationContext()>");
        VirtualInvokeExpr vinvokeExpr = null;
        ArrayList<Unit> units = new ArrayList<>();

        for(Iterator<Unit> iter =getMy_units().iterator(); iter.hasNext();){

            Unit u = iter.next();
            if(u.toString().contains("getApplicationContext")){
                try {
                    vinvokeExpr = Jimple.v().newVirtualInvokeExpr(thisLocal,get_context.makeRef());
                    AssignStmt astmt = Jimple.v().newAssignStmt(u.getDefBoxes().get(0).getValue(), vinvokeExpr);
                    units.add(astmt);
                }catch (Exception e){
                   iter.remove();
                }

            }else{
                units.add(u);
            }
        }
        setMy_units(units);
    }





}
