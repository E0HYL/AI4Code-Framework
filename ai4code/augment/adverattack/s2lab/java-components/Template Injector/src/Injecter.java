import soot.*;
import soot.jimple.*;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.concurrent.ThreadLocalRandom;

public class Injecter {

    private Soot_utlilty config = new Soot_utlilty();
    private ArrayList<SootClass> already_injected = new ArrayList<>();


    public boolean inject_slice(My_slice to_inject, SootMethod injected,String opaque_path){
        ArrayList<Unit> units_to_inj = to_inject.getMy_units();
        ArrayList<Local> locals_to_inj = to_inject.getMy_locals();
        if(!injected.hasActiveBody()){
            System.out.println("This method has no active body!");
            return false;
        }

        Body b = injected.getActiveBody();

        for (Local lo : locals_to_inj){
            if(!b.getLocals().contains(lo)){
                b.getLocals().add(lo);
            }
        }
        ArrayList<Unit> extremis = this.findExtremis(b);
        if(!extremis.isEmpty() && !(extremis.size() == 1)){
            Unit start = extremis.get(0);
            Unit end = extremis.get(1);
            Jimple_utility j_utility = new Jimple_utility();
            try {
                b.getUnits().insertAfter(units_to_inj, start);
                if(!(extremis.get(0) instanceof ReturnVoidStmt)) {
                    int size = units_to_inj.size();
                    Unit final_u = units_to_inj.get(size - 1);

                    b.getUnits().remove(final_u);
                }else{
                    b.getUnits().remove(extremis.get(0));
                }
            }catch (Exception e){
                return false;
            }
            if(Instrumenter.DEBUG) {
                System.out.println("Final Jimple code\n" + b.toString());

            }
            b.validate();
            return true;
        }
        return false;
    }

    private ArrayList<Unit> findExtremis(Body activeBody) {
        ArrayList<Unit> tmp = new ArrayList<>();
        UnitPatchingChain units =activeBody.getUnits();
        int max_number = units.size();
        int min =0;
        for(Iterator<Unit> iter = units.iterator();iter.hasNext();){
            Unit tmp_u =iter.next();
            if(tmp_u instanceof IdentityStmt){
                min++;
            }else{
                break;
            }
        }

        int randomNum = ThreadLocalRandom.current().nextInt(min, max_number);
        int i=0;
        for(Iterator<Unit> iter = units.iterator();iter.hasNext();){
            Unit tmp_u =iter.next();
            if(i==randomNum || i== randomNum+1){
                tmp.add(tmp_u);
            }
            i++;
        }
        return  tmp;
    }



    public boolean inject(ArrayList<SootClass> possible_inj,My_slice slice,String opaque_path){
        boolean done = false;
        for(int i=0; i< possible_inj.size(); i++){
            SootClass tmp_c = possible_inj.get(i);
            if(config.isExcludedLibrary_noASexc(tmp_c.getName()) || already_injected.contains(tmp_c) || tmp_c.isLibraryClass()||  tmp_c.getName().contains("MainActivity"))  continue;
            for(SootMethod m : tmp_c.getMethods()){
                if(!m.hasActiveBody() || config.isExcludedMethod(m.getName())){
                    continue;
                }
                slice.fix_this_ref(tmp_c);
                Injecter inj = new Injecter();
                done =inj.inject_slice(slice,m,opaque_path);
                if(done) break;
            }
            if(done){
                System.out.println("Chosen class "+tmp_c.getName());

                already_injected.add(tmp_c);
                break;
            }

        }
        return done;
    }

}
